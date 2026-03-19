from typing import List
from datetime import datetime
import hashlib
import base64

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks

from app.database import bronze_collection, silver_collection
from app.models.bronze import BronzeDocument, BronzeResponse
from app.services.processor import process_ocr

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/")
async def upload_documents(
    files: List[UploadFile] = File(...),
    dossierId: str = Form(...),
    entrepriseId: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    results = []

    for file in files:
        # 1. Vérifier le type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non autorisé pour {file.filename}"
            )

        # 2. Lire le contenu
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail=f"Fichier vide : {file.filename}"
            )

        # 3. Vérifier la taille
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux : {file.filename} ({len(content) // (1024*1024)}MB). Maximum : 50MB"
            )

        # 4. Calculer le hash
        sha256 = hashlib.sha256(content).hexdigest()

        # 5. Vérifier doublon
        existing = await bronze_collection.find_one({"sha256_hash": sha256})
        if existing:
            continue

        # 6. Encoder en base64
        file_b64 = base64.b64encode(content).decode("utf-8")

        # 7. Construire Bronze
        doc = BronzeDocument(
            filename=file.filename,
            content_type=file.content_type,
            file_data=file_b64,
            file_size=len(content),
            sha256_hash=sha256,
            dossierId=dossierId,
            entrepriseId=entrepriseId,
        )

        # 8. Insert Bronze
        result = await bronze_collection.insert_one(doc.model_dump())

        # 9. Créer Silver pending
        await silver_collection.insert_one({
            "bronze_id": str(result.inserted_id),
            "filename": file.filename,
            "document_type": None,
            "ocr_text": None,
            "extracted_fields": {},
            "ocr_confidence": None,
            "processed_at": None,
            "status": "pending",
            "dossierId": dossierId,
            "entrepriseId": entrepriseId
        })

        # 10. Lancer OCR en background
        if background_tasks:
            background_tasks.add_task(
                process_ocr,
                content,
                file.filename,
                result.inserted_id,
                dossierId,
                entrepriseId
            )

        # 11. Réponse
        results.append(
            BronzeResponse(
                id=str(result.inserted_id),
                filename=file.filename,
                sha256_hash=sha256,
                dossierId=dossierId,
                entrepriseId=entrepriseId,
                uploaded_at=doc.uploaded_at,
                status=doc.status
            ).model_dump()
        )

    if not results:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier valide uploadé (ou tous déjà présents)"
        )

    return {
        "message": "Upload réussi",
        "count": len(results),
        "files": results
    }