from fastapi import APIRouter, HTTPException
from app.database import entreprises_collection
from app.models.entreprise import EntrepriseCreate, EntrepriseDocument, EntrepriseResponse
from datetime import datetime
from bson import ObjectId

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


# ── Lister toutes les entreprises ──
@router.get("/", response_model=list[EntrepriseResponse])
async def get_entreprises():
    entreprises = await entreprises_collection.find().to_list(100)
    return [
        EntrepriseResponse(
            id=str(e["_id"]),
            **{k: v for k, v in e.items() if k != "_id"}
        ) for e in entreprises
    ]


# ── Récupérer une entreprise par ID ──
@router.get("/{entreprise_id}", response_model=EntrepriseResponse)
async def get_entreprise(entreprise_id: str):
    entreprise = await entreprises_collection.find_one({"_id": ObjectId(entreprise_id)})
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return EntrepriseResponse(
        id=str(entreprise["_id"]),
        **{k: v for k, v in entreprise.items() if k != "_id"}
    )


# ── Récupérer une entreprise par SIRET ──
@router.get("/siret/{siret}", response_model=EntrepriseResponse)
async def get_entreprise_by_siret(siret: str):
    entreprise = await entreprises_collection.find_one({"siret": siret})
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return EntrepriseResponse(
        id=str(entreprise["_id"]),
        **{k: v for k, v in entreprise.items() if k != "_id"}
    )