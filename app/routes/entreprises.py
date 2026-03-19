from fastapi import APIRouter, HTTPException
from app.database import entreprises_collection
from app.models.entreprise import EntrepriseCreate, EntrepriseDocument, EntrepriseResponse
from datetime import datetime

router = APIRouter(prefix="/entreprises", tags=["Entreprises"])


@router.post("/", response_model=EntrepriseResponse)
async def create_entreprise(data: EntrepriseCreate):
    existing = await entreprises_collection.find_one({"external_id": data.external_id})

    if existing:
        raise HTTPException(status_code=409, detail="Entreprise déjà existante")

    now = datetime.utcnow()

    doc = EntrepriseDocument(
        external_id=data.external_id,
        siret=data.siret,
        siren=data.siren,
        denomination_sociale=data.denomination_sociale,
        created_at=now,
        updated_at=now
    )

    result = await entreprises_collection.insert_one(doc.model_dump())

    return EntrepriseResponse(
        id=str(result.inserted_id),
        **doc.model_dump()
    )