from fastapi import APIRouter, HTTPException
from app.database import dossiers_collection
from app.models.dossier import DossierCreate, DossierDocument, DossierResponse
from datetime import datetime

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


@router.post("/", response_model=DossierResponse)
async def create_dossier(data: DossierCreate):
    existing = await dossiers_collection.find_one({"external_id": data.external_id})

    if existing:
        raise HTTPException(status_code=409, detail="Dossier déjà existant")

    now = datetime.utcnow()

    doc = DossierDocument(
        external_id=data.external_id,
        entreprise_id=data.entreprise_id,
        nom=data.nom,
        created_by=data.created_by,
        created_at=now,
        updated_at=now
    )

    result = await dossiers_collection.insert_one(doc.model_dump())

    return DossierResponse(
        id=str(result.inserted_id),
        **doc.model_dump()
    )