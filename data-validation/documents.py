from flask import Blueprint, request, jsonify
from validator import ServiceValidation

documents_bp = Blueprint('documents', __name__)

validateur = ServiceValidation()

@documents_bp.route('/api/v1/documents/batch', methods=['POST'])
def process_documents_batch():
    """
    Endpoint qui reçoit une liste de documents extraits par l'OCR.
    Format attendu : JSON contenant un tableau d'objets.
    """
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({"erreur": "Format invalide. Un tableau JSON est attendu."}), 400

    alertes = validateur.valider_lot_documents(data)

    reponse = {
        "code": 200,
        "statut": "success",
        "documents_traites": len(data),
        "anomalies_detectees": len(alertes),
        "details_alertes": alertes
    }

    return jsonify(reponse), 200