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
app.json.ensure_ascii = False

OUTPUT_DIR = Path(os.environ.get("PAPERFLOW_OUTPUT_DIR", "output4"))
OCR_RESULT_PATH = OUTPUT_DIR / "rib_result.json"
EXTRACTED_BLOCKS_PATH = OUTPUT_DIR / "rib_blocks.json"
REGEX_CONFIG_PATH = Path("analyse")

print("Chargement du modèle PaddleOCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)
print("Modèle chargé avec succès.")

analyzers = {
    "facture": AnalyzeFacture(ocr, REGEX_CONFIG_PATH / "facture_simple.json"),
    "devis": AnalyzeDevis(ocr, REGEX_CONFIG_PATH / "devis.json"),
    "kbis": AnalyzeKBIS(ocr, REGEX_CONFIG_PATH / "kbis.json"),
    "siret": AnalyzeSIRET(ocr, REGEX_CONFIG_PATH / "siret.json"),
    "urssaf": AnalyzeURSSAF(ocr, REGEX_CONFIG_PATH / "urssaf.json"),
    "rib": AnalyzeRIB(ocr, REGEX_CONFIG_PATH / "rib.json")
}

@app.route('/api/v1/analyze/<doc_type>', methods=['POST'])
def analyze_document(doc_type):
    data = request.get_json()
    
    if not data or 'image_base64' not in data:
        return jsonify({"error": "Aucune image base64 fournie."}), 400
        
    base64_string = data['image_base64']
    
    try:
        analyzer = analyzers[doc_type]
        extraction_result = analyzer.analyze_base64(base64_string)

        return jsonify({
            "status": "success",
            "document_type": doc_type,
            "data": extraction_result
        }), 200

    except KeyError:
        return jsonify({"error": f"Type de document '{doc_type}' non supporté."}), 400
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'analyse du document: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)