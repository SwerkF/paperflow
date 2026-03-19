from typing import List
from datetime import datetime
import hashlib
import base64

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks

from app.database import bronze_collection, silver_collection
from app.models.bronze import BronzeDocument, BronzeResponse, DocumentType
from app.services.processor import process_ocr

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/")
async def upload_documents(
    files: List[UploadFile] = File(...),
    dossierId: int = Form(...),
    entrepriseId: int = Form(...),
    document_type: DocumentType = Form(DocumentType.autre),  # ← ajouté
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

        # 3. Calculer le hash
        sha256 = hashlib.sha256(content).hexdigest()

        # 4. Vérifier doublon
        existing = await bronze_collection.find_one({"sha256_hash": sha256})
        if existing:
            continue

        # 5. Encoder en base64
        file_b64 = base64.b64encode(content).decode("utf-8")

        # 6. Construire Bronze
        doc = BronzeDocument(
            filename=file.filename,
            content_type=file.content_type,
            file_data=file_b64,
            file_size=len(content),
            sha256_hash=sha256,
            dossierId=dossierId,
            entrepriseId=entrepriseId,
            document_type=document_type,  # ← ajouté
        )

        # 7. Insert Bronze
        result = await bronze_collection.insert_one(doc.model_dump())

        # 8. Créer Silver pending
        await silver_collection.insert_one({
            "bronze_id": str(result.inserted_id),
            "filename": file.filename,
            "document_type": document_type.value,  # ← ajouté
            "ocr_text": None,
            "extracted_fields": {},
            "ocr_confidence": None,
            "processed_at": None,
            "status": "pending",
            "dossierId": dossierId,
            "entrepriseId": entrepriseId
        })

        # 9. Lancer OCR en background
        if background_tasks:
            background_tasks.add_task(
                process_ocr,
                content,
                file.filename,
                result.inserted_id,
                dossierId,
                entrepriseId
            )

        # 10. Réponse
        results.append(
            BronzeResponse(
                id=str(result.inserted_id),
                filename=file.filename,
                sha256_hash=sha256,
                dossierId=dossierId,
                entrepriseId=entrepriseId,
                document_type=document_type,  # ← ajouté
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