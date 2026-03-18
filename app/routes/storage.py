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