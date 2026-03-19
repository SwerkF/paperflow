from typing import List
from datetime import datetime
import hashlib
import base64

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks

from app.database import bronze_collection, silver_collection, entreprises_collection
from app.models.bronze import BronzeDocument, BronzeResponse
from app.services.processor import process_ocr
from bson import ObjectId

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/")
async def upload_documents(
    files: List[UploadFile] = File(...),
    dossierId: str = Form(...),
    entrepriseId: str = Form(...),
    siret_principal: str = Form(None),
    nom_principal: str = Form(None),
    background_tasks: BackgroundTasks = None
):
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    results = []

    # --- Récupération du contexte Entreprise ---
    entreprise = None
    if ObjectId.is_valid(entrepriseId):
        entreprise = await entreprises_collection.find_one({"_id": ObjectId(entrepriseId)})
    
    # Si le SIRET n'a pas été fourni explicitement, on le prend dans la collection Entreprise
    if not siret_principal and entreprise:
        siret_principal = entreprise.get("siret")
        nom_principal = entreprise.get("denomination_sociale")

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

        # 4. Vérifier doublon
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

        # 9. Lancer Airflow en background
        if background_tasks:
            import requests
            def trigger_airflow(b_id, f_b64, fname, d_id, e_id, siret, nom):
                try:
                    airflow_url = "http://airflow-webserver:8080/api/v1/dags/hackathon_flow_complet/dagRuns"
                    airflow_payload = {
                        "conf": {
                            "bronze_id": b_id,
                            "filename": fname,
                            "dossierId": d_id,
                            "entrepriseId": e_id,
                            "siret_principal": siret,
                            "nom_principal": nom
                        }
                    }
                    resp = requests.post(
                        airflow_url,
                        json=airflow_payload,
                        auth=("airflow", "airflow")
                    )
                    resp.raise_for_status()
                    print(f"DAG Airflow déclenché avec succès pour {fname}")
                except Exception as e:
                    print(f"Erreur lors du déclenchement du DAG Airflow : {e}")
                    
            background_tasks.add_task(
                trigger_airflow,
                str(result.inserted_id),
                file_b64,
                file.filename,
                dossierId,
                entrepriseId,
                siret_principal,
                nom_principal
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
