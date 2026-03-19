from flask import Blueprint, request, jsonify
from validator import ServiceValidation

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/api/v1/documents/batch', methods=['POST'])
def process_documents_batch():
    """
    Endpoint qui reçoit un batch contextualisé de documents extraits par l'OCR.
    Format attendu : JSON contenant un objet avec:
      - contexte_utilisateur (objet)
      - documents (tableau)
    """
    validator = ServiceValidation()

    data = request.get_json()

    if not data or not isinstance(data, dict):
        return (
            jsonify(
                {
                    "erreur": "Format invalide. Un objet JSON est attendu.",
                    "attendu": {"contexte_utilisateur": {}, "documents": []},
                }
            ),
            400,
        )

    contexte_utilisateur = data.get("contexte_utilisateur")
    documents = data.get("documents")

    if not isinstance(contexte_utilisateur, dict):
        return jsonify({"erreur": "Format invalide. 'contexte_utilisateur' doit être un objet."}), 400
    if not isinstance(documents, list):
        return jsonify({"erreur": "Format invalide. 'documents' doit être un tableau."}), 400

    alertes, contextes_verifies = validator.validate_documents(contexte_utilisateur, documents)

    reponse = {
        "code": 200,
        "statut": "success",
        "documents_traites": len(documents),
        "anomalies_detectees": len(alertes),
        "details_alertes": alertes,
        "contextes_verifies": contextes_verifies
    }

    return jsonify(reponse), 200