from fastapi import APIRouter, HTTPException
from app.database import bronze_collection, silver_collection, gold_collection
from bson import ObjectId

router = APIRouter(prefix="/storage", tags=["Storage"])

def serialize(doc) -> dict:
    doc["id"] = str(doc.pop("_id"))
    # on ne renvoie pas le fichier base64 dans les listes
    doc.pop("file_data", None)
    return doc

# --- BRONZE ---
@router.get("/bronze")
async def get_bronze_documents():
    docs = await bronze_collection.find().to_list(100)
    return [serialize(d) for d in docs]

@router.get("/bronze/{doc_id}")
async def get_bronze_document(doc_id: str):
    doc = await bronze_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return serialize(doc)

@router.get("/bronze/{doc_id}/image")
async def get_bronze_document_image(doc_id: str):
    doc = await bronze_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc or "file_data" not in doc:
        raise HTTPException(status_code=404, detail="Image introuvable")
    return {"file_data": doc["file_data"]}

# --- SILVER ---
@router.get("/silver")
async def get_silver_documents():
    docs = await silver_collection.find().to_list(100)
    return [serialize(d) for d in docs]

@router.get("/silver/{doc_id}")
async def get_silver_document(doc_id: str):
    doc = await silver_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return serialize(doc)

@router.get("/silver/{doc_id}/image")
async def get_silver_document_image(doc_id: str):
    doc = await silver_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc or "bronze_id" not in doc:
        raise HTTPException(status_code=404, detail="Document Silver introuvable ou sans référence Bronze")

    bronze_doc = await bronze_collection.find_one({"_id": ObjectId(doc["bronze_id"])})
    if not bronze_doc or "file_data" not in bronze_doc:
        raise HTTPException(status_code=404, detail="Image introuvable dans Bronze")

    return {
        "file_data": bronze_doc["file_data"],
        "content_type": bronze_doc.get("content_type", "application/pdf")
    }

@router.patch("/silver/{doc_id}/validate")
async def validate_silver_document(doc_id: str):
    doc = await silver_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    
    # On passe en valide et on l'envoie en Gold Optionnellement
    await silver_collection.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"status": "VALIDE", "alertes": []}}
    )
    
    # Simple insertion dans Gold pour simuler la fin du pipe
    doc_gold = dict(doc)
    doc_gold["_id"] = ObjectId()
    doc_gold["status"] = "VALIDE"
    doc_gold["alertes"] = []
    await gold_collection.insert_one(doc_gold)

    return {"message": "Document supervisé et validé avec succès"}

# --- GOLD ---
@router.get("/gold")
async def get_gold_documents():
    docs = await gold_collection.find().to_list(100)
    return [serialize(d) for d in docs]

@router.get("/gold/{doc_id}")
async def get_gold_document(doc_id: str):
    doc = await gold_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return serialize(doc)