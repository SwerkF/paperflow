from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import List
from app.database import bronze_collection, silver_collection
from app.models.bronze import BronzeResponse
from datetime import datetime
import hashlib
import base64

# (optionnel mais recommandé pour la suite)
from app.services.processor import process_ocr

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/")
async def upload_documents(
    files: List[UploadFile] = File(...),
    dossierId: int = Form(...),
    entrepriseId: int = Form(...),
    background_tasks: BackgroundTasks = None
):
    results = []

    allowed_types = ["application/pdf", "image/jpeg", "image/png"]

    for file in files:
        # 1. Lire fichier
        content = await file.read()

        # 2. Vérifier type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Type non autorisé: {file.filename}"
            )

        # 3. Hash SHA256
        sha256 = hashlib.sha256(content).hexdigest()

        # 4. Vérifier doublon
        existing = await bronze_collection.find_one({"sha256_hash": sha256})
        if existing:
            print(f"⚠️ Doublon ignoré: {file.filename}")
            continue

        # 5. Base64
        file_b64 = base64.b64encode(content).decode("utf-8")

        # 6. Document Bronze
        doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_data": file_b64,
            "file_size": len(content),
            "sha256_hash": sha256,
            "dossierId": dossierId,
            "entrepriseId": entrepriseId,
            "uploaded_at": datetime.utcnow(),
            "status": "pending"
        }

        # 7. Insert Bronze
        result = await bronze_collection.insert_one(doc)

        # 8. Insert Silver (placeholder OCR)
        await silver_collection.insert_one({
            "bronze_id": str(result.inserted_id),
            "filename": file.filename,
            "document_type": None,
            "ocr_text": None,
            "extracted_fields": {},
            "status": "pending",
            "processed_at": None
        })

        # 9. Lancer OCR en background (IMPORTANT 🔥)
        if background_tasks:
            background_tasks.add_task(
                process_ocr,
                content,
                file.filename,
                result.inserted_id
            )

        # 10. Résultat
        results.append({
            "id": str(result.inserted_id),
            "filename": file.filename,
            "sha256": sha256
        })

    if not results:
        raise HTTPException(status_code=400, detail="Aucun fichier valide uploadé")

    return {
        "message": "Upload réussi",
        "count": len(results),
        "files": results
    }