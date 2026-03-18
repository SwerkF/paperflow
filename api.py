import json
import os
import tempfile
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



OUTPUT_DIR = Path(os.environ.get("PAPERFLOW_OUTPUT_DIR", "output4"))
OCR_RESULT_PATH = OUTPUT_DIR / "rib_result.json"
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "rib_blocks.json"
REGEX_CONFIG_PATH = Path("analyse")

analyzers = {
    "facture": AnalyzeFacture(REGEX_CONFIG_PATH / "facture.json"),
    "devis": AnalyzeDevis(REGEX_CONFIG_PATH / "devis.json"),
    "kbis": AnalyzeKBIS(REGEX_CONFIG_PATH / "kbis.json"),
    "siret": AnalyzeSIRET(REGEX_CONFIG_PATH / "siret.json"),
    "urssaf": AnalyzeURSSAF(REGEX_CONFIG_PATH / "urssaf.json"),
    "rib": AnalyzeRIB(REGEX_CONFIG_PATH / "rib.json")
}

print("Chargement du modèle PaddleOCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)
print("Modèle chargé avec succès.")


@app.route('/api/v1/analyze/<doc_type>', methods=['POST'])
def analyze_document(doc_type):
    if doc_type not in analyzers:
        return jsonify({
            "error": f"Type de document non supporté. Types valides : {list(analyzers.keys())}"
        }), 400

    # 2. Vérifier si la requête contient bien un fichier image
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image fournie dans la requête (clé 'image' manquante)."}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné."}), 400

    # 3. Traitement dans un dossier temporaire propre
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        image_path = temp_dir_path / file.filename
        
        # Sauvegarde temporaire de l'image
        file.save(str(image_path))

        try:
            # 4. Appel magique à la bonne classe !
            # Pas besoin de faire l'OCR manuellement, la méthode analyze() s'en charge.
            analyzer = analyzers[doc_type]
            extraction_result = analyzer.analyze(str(image_path))

            # 5. Renvoi du résultat au client
            return jsonify({
                "status": "success",
                "document_type": doc_type,
                "data": extraction_result
            }), 200
            
        except Exception as e:
            # Gestion des erreurs
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)