import os
import tempfile
import base64
import json
from pathlib import Path
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR

from python_classes.analyse_facture import AnalyzeFacture
from python_classes.analyze_devis import AnalyzeDevis
from python_classes.analyze_kbis import AnalyzeKBIS
from python_classes.analyze_siret import AnalyzeSIRET
from python_classes.analyze_urssaf import AnalyzeURSSAF
from python_classes.analyze_rib import AnalyzeRIB

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

app = Flask(__name__)
app.json.ensure_ascii = False

REGEX_CONFIG_PATH = Path("analyse")

print("Initialisation des analyseurs...")
analyzers = {
    "facture": AnalyzeFacture(REGEX_CONFIG_PATH / "facture.json"),
    "devis": AnalyzeDevis(REGEX_CONFIG_PATH / "devis.json"),
    "kbis": AnalyzeKBIS(REGEX_CONFIG_PATH / "kbis.json"),
    "siret": AnalyzeSIRET(REGEX_CONFIG_PATH / "siret.json"),
    "urssaf": AnalyzeURSSAF(REGEX_CONFIG_PATH / "urssaf.json"),
    "rib": AnalyzeRIB(REGEX_CONFIG_PATH / "rib.json")
}

# Initialisation OCR
print("Chargement du modèle PaddleOCR (Moteur Central)...")
ocr_model = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)
print("API prête !")

# Extration des donnée de l'OCR 
def extract_raw_ocr_data(image_path: str):
    """Exécute l'OCR et extrait les données brutes."""
    results = ocr_model.predict(input=str(image_path))
    raw_rec_texts = []
    raw_records = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        for index, res in enumerate(results):
            result_path = temp_dir_path / f"temp_result_{index}.json"
            res.save_to_json(str(result_path))
            
            with result_path.open("r", encoding="utf-8") as handle:
                page_data = json.load(handle)
                
            page_texts = page_data.get("rec_texts", [])
            page_boxes = page_data.get("rec_boxes", [])
            
            if isinstance(page_texts, list):
                for i, item in enumerate(page_texts):
                    text_str = str(item)
                    raw_rec_texts.append(text_str)
                    
                    if isinstance(page_boxes, list) and i < len(page_boxes):
                        box = page_boxes[i]
                        if isinstance(box, list) and len(box) == 4:
                            raw_records.append({
                                "text": text_str,
                                "x1": float(box[0]), "y1": float(box[1]),
                                "x2": float(box[2]), "y2": float(box[3]),
                                "x_center": (float(box[0]) + float(box[2])) / 2,
                            })
    return raw_rec_texts, raw_records


# Utilisation d'extract_raw pour détaerminer le type de document
def detect_document_type(raw_rec_texts: list[str]) -> str:
    """Analyse les mots clés du document pour déduire so type."""
    text = " ".join(raw_rec_texts).lower()
    
    if "kbis" in text or "greffe du tribunal" in text or "immatriculation au rcs" in text:
        return "kbis"
    elif "attestation de vigilance" in text or "urssaf" in text:
        return "urssaf"
    elif "attestation d'immatriculation" in text or ("siren" in text and "rne" in text):
        return "siret"
    elif "relevé d'identité bancaire" in text or ("iban" in text and "bic" in text and "rib" in text):
        return "rib"
    elif "devis" in text or "proposition commerciale" in text:
        return "devis"
    elif "facture" in text:
        return "facture"
    return "inconnu"


@app.route('/api/v1/analyze', methods=['POST'])
def analyze_document():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        image_path = None

        # Assurer que la requête contient le fichier en base64
        if request.is_json:
            data = request.get_json()
            if 'image_base64' not in data:
                return jsonify({"error": "Aucune image fournie."}), 400
            base64_string = data['image_base64'].split(",")[1] if "," in data['image_base64'] else data['image_base64']
            try:
                img_bytes = base64.b64decode(base64_string)
                if base64_string.startswith("JVBERi0"):
                    image_path = temp_dir_path / "document.pdf"
                else:
                    image_path = temp_dir_path / "document.png"

                with open(image_path, "wb") as f:
                    f.write(img_bytes)
                    
                if not base64_string.startswith("JVBERi0"):
                    try:
                        from PIL import Image
                        with Image.open(image_path) as img:
                            max_size = 2000
                            if max(img.size) > max_size:
                                print(f"Resizing image from {img.size} limits...")
                                img.thumbnail((max_size, max_size), getattr(Image, 'Resampling', Image).LANCZOS)
                                img.save(image_path)
                    except Exception as resize_err:
                        print(f"Warning: Could not resize image: {resize_err}")

            except Exception as e:
                return jsonify({"error": f"Erreur décodage Base64: {str(e)}"}), 400
        elif 'image' in request.files:
            file = request.files['image']
            image_path = temp_dir_path / file.filename
            file.save(str(image_path))
        else:
            return jsonify({"error": "Format non supporté."}), 400

        try:
            raw_rec_texts, raw_records = extract_raw_ocr_data(str(image_path))
            
            # classification
            doc_type = detect_document_type(raw_rec_texts)
            
            if doc_type == "inconnu":
                return jsonify({
                    "status": "error",
                    "message": "Type de document non reconnu ou non supporté.",
                    "debug_text": " ".join(raw_rec_texts)[:300]
                }), 400

            # formatage
            analyzer = analyzers[doc_type]
            extraction_result = analyzer.analyze_from_data(raw_rec_texts, raw_records)

            return jsonify({
                "status": "success",
                "document_type": doc_type,
                "data": extraction_result
            }), 200
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    
    print("Démarrage du WSGI de production sur le port 8000")
    print("Écoute sur http://0.0.0.0:8000")
    
    serve(app, host='0.0.0.0', port=8000)