from fastapi import APIRouter, HTTPException, Depends
from app.database import users_collection
from app.models.user import UserCreate, UserDocument, UserResponse
from app.auth import create_access_token, get_current_user, require_admin
from datetime import datetime
import hashlib
from bson import ObjectId

router = APIRouter(prefix="/users", tags=["Users"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ── Créer le premier admin (seulement si aucun admin existe) ──
@router.post("/init-admin")
async def init_admin(user: UserCreate):
    existing_admin = await users_collection.find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(
            status_code=403,
            detail="Un admin existe déjà"
        )
    now = datetime.utcnow()
    new_user = UserDocument(
        email=user.email,
        password_hash=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        role="admin",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    result = await users_collection.insert_one(new_user.model_dump())
    return {"message": "Admin créé avec succès", "id": str(result.inserted_id)}

# ── Créer un utilisateur (admin seulement) ──
@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_admin)
):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    now = datetime.utcnow()
    new_user = UserDocument(
        email=user.email,
        password_hash=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    result = await users_collection.insert_one(new_user.model_dump())
    return UserResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_user.model_dump().items()
           if k in UserResponse.model_fields}
    )

# ── Login ──
@router.post("/login")
async def login(email: str, password: str):
    user = await users_collection.find_one({
        "email": email,
        "password_hash": hash_password(password)
    })
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Compte désactivé")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}

# ── Profil utilisateur connecté ──
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        first_name=current_user["first_name"],
        last_name=current_user["last_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"]
    )

# ── Lister tous les users (admin seulement) ──
@router.get("/", response_model=list[UserResponse])
async def get_all_users(current_user: dict = Depends(require_admin)):
    users = await users_collection.find().to_list(100)
    return [
        UserResponse(
            id=str(u["_id"]),
            email=u["email"],
            first_name=u["first_name"],
            last_name=u["last_name"],
            role=u["role"],
            is_active=u["is_active"],
            created_at=u["created_at"],
            updated_at=u["updated_at"]
        ) for u in users
    ]

# ── Désactiver un user (admin seulement) ──
@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"message": "Utilisateur désactivé"}