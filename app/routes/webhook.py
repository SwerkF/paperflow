from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.database import bronze_collection, silver_collection, gold_collection
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/webhook", tags=["Webhook"])

class WebhookPayload(BaseModel):
    bronze_id: str
    statut_final: str
    alertes: Optional[list] = None
    extracted_data: Optional[dict] = None

@router.post("/airflow_result")
async def handle_airflow_result(payload: WebhookPayload):
    # 1. Update Silver
    silver_update = {
        "status": payload.statut_final,
        "processed_at": datetime.utcnow()
    }
    if payload.extracted_data is not None:
        silver_update["extracted_fields"] = payload.extracted_data
        if "type" in payload.extracted_data:
            silver_update["document_type"] = payload.extracted_data["type"]
            
    if payload.alertes is not None:
        silver_update["alertes"] = payload.alertes
        
    await silver_collection.update_one(
        {"bronze_id": payload.bronze_id},
        {"$set": silver_update}
    )
    
    # Update Bronze status
    await bronze_collection.update_one(
        {"_id": ObjectId(payload.bronze_id)},
        {"$set": {"status": payload.statut_final}}
    )

    # 2. If valid, create Gold
    if payload.statut_final == "VALIDE":
        silver_doc = await silver_collection.find_one({"bronze_id": payload.bronze_id})
        if silver_doc:
            doc_type = "unknown"
            if payload.extracted_data and "type" in payload.extracted_data:
                doc_type = payload.extracted_data["type"]
            
            gold_doc = {
                "silver_id": str(silver_doc["_id"]),
                "bronze_id": payload.bronze_id,
                "filename": silver_doc.get("filename"),
                "document_type": doc_type,
                "validated_fields": payload.extracted_data or {},
                "coherence_score": 1.0,
                "incoherences": payload.alertes or [],
                "is_fraudulent": False,
                "curated_at": datetime.utcnow(),
                "status": "valid",
                "dossierId": silver_doc.get("dossierId"),
                "entrepriseId": silver_doc.get("entrepriseId")
            }
            await gold_collection.insert_one(gold_doc)
            
    return {"message": "Webhook processed successfully"}
