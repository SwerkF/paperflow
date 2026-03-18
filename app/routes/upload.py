from fastapi import APIRouter, UploadFile, File, HTTPException
from app.database import bronze_collection, silver_collection
from app.models.bronze import BronzeDocument, BronzeResponse
from datetime import datetime
import hashlib
import base64

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/", response_model=BronzeResponse)
async def upload_document(file: UploadFile = File(...)):

    # 1. Lire le fichier
    content = await file.read()

    # 2. Vérifier le type autorisé
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

    # 3. Calculer le hash SHA-256
    sha256 = hashlib.sha256(content).hexdigest()

    # 4. Vérifier si le document existe déjà
    existing = await bronze_collection.find_one({"sha256_hash": sha256})
    if existing:
        raise HTTPException(status_code=409, detail="Document déjà uploadé")

    # 5. Encoder en base64 pour stockage MongoDB
    file_b64 = base64.b64encode(content).decode("utf-8")

    # 6. Créer le document Bronze
    doc = BronzeDocument(
        filename=file.filename,
        content_type=file.content_type,
        file_data=file_b64,
        file_size=len(content),
        sha256_hash=sha256,
    )

    # 7. Insérer dans MongoDB
    result = await bronze_collection.insert_one(doc.model_dump())

    # 8. Créer automatiquement une entrée Silver vide (prête pour l'OCR)
    await silver_collection.insert_one({
        "bronze_id": str(result.inserted_id),
        "filename": file.filename,
        "document_type": None,
        "ocr_text": None,
        "extracted_fields": {},
        "status": "pending",
        "processed_at": datetime.utcnow()
    })

    return BronzeResponse(
        id=str(result.inserted_id),
        filename=file.filename,
        sha256_hash=sha256,
        uploaded_at=doc.uploaded_at,
        status=doc.status
    )