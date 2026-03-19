from fastapi import APIRouter, HTTPException
from app.database import dossiers_collection, entreprises_collection
from app.models.dossier import DossierCreate, DossierDocument, DossierResponse
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


@router.post("/", response_model=DossierResponse)
async def create_dossier(data: DossierCreate):
    now = datetime.utcnow()

    doc = DossierDocument(
        entreprise_id=data.entreprise_id,
        nom=data.nom,
        created_by=data.created_by,
        created_at=now,
        updated_at=now
    )

    result = await dossiers_collection.insert_one(doc.model_dump())

    # ── Ajouter automatiquement le dossier dans l'entreprise ──
    await entreprises_collection.update_one(
        {"_id": ObjectId(data.entreprise_id)},
        {
            "$addToSet": {"dossiers_ids": str(result.inserted_id)},
            "$set": {"updated_at": now}
        }
    )

    return DossierResponse(
        id=str(result.inserted_id),
        **doc.model_dump()
    )


# ── Lister tous les dossiers ──
@router.get("/", response_model=list[DossierResponse])
async def get_dossiers():
    dossiers = await dossiers_collection.find().to_list(100)
    return [
        DossierResponse(
            id=str(d["_id"]),
            **{k: v for k, v in d.items() if k != "_id"}
        ) for d in dossiers
    ]


# ── Récupérer un dossier par ID ──
@router.get("/{dossier_id}", response_model=DossierResponse)
async def get_dossier(dossier_id: str):
    dossier = await dossiers_collection.find_one({"_id": ObjectId(dossier_id)})
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return DossierResponse(
        id=str(dossier["_id"]),
        **{k: v for k, v in dossier.items() if k != "_id"}
    )


# ── Récupérer tous les dossiers d'une entreprise ──
@router.get("/entreprise/{entreprise_id}", response_model=list[DossierResponse])
async def get_dossiers_by_entreprise(entreprise_id: str):
    dossiers = await dossiers_collection.find(
        {"entreprise_id": entreprise_id}
    ).to_list(100)
    return [
        DossierResponse(
            id=str(d["_id"]),
            **{k: v for k, v in d.items() if k != "_id"}
        ) for d in dossiers
    ]