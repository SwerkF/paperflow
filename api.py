import json
import os
import tempfile
from pathlib import Path

from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from ORCMethods import ORCMethods

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"

app = Flask(__name__)

OCRMethodsInstance = ORCMethods(ocr=None)

print("Chargement du modèle PaddleOCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)
print("Modèle chargé avec succès.")

@app.route('/api/v1/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image fournie dans la requête."}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné."}), 400

    if file:
        # Utilisation d'un dossier temporaire pour gérer les fichiers sans polluer le serveur
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Sauvegarder l'image reçue temporairement
            image_path = temp_dir_path / file.filename
            file.save(str(image_path))

            try:
                # Analyse de l'image
                results = ocr.predict(input=str(image_path))
                
                json_results = []
                for index, res in enumerate(results):
                    # Sauvegarder le résultat temporairement pour le parser (comme dans le script original)
                    result_path = temp_dir_path / f"result_{index}.json"
                    res.save_to_json(str(result_path))

                    # Lecture du fichier JSON généré
                    with result_path.open("r", encoding="utf-8") as handle:
                        json_results.append(json.load(handle))

                if(json_results.type == 'Devis'):
                    testDevisResult = OCRMethodsInstance.testDevis(json_results)
                    print(testDevisResult)

                # Renvoi du résultat avec un statut HTTP 200
                return jsonify({
                    "status": "success",
                    "data": testDevisResult
                }), 200
                
            except Exception as e:
                # Gestion des erreurs liées à la prédiction
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)