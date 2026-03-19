from fastapi import APIRouter, HTTPException
from app.database import users_collection
from app.models.user import UserCreate, UserDocument, UserResponse
from datetime import datetime
import hashlib

router = APIRouter(prefix="/users", tags=["Users"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    existing_user = await users_collection.find_one({"email": user.email})

    if existing_user:
        raise HTTPException(status_code=409, detail="Cet email existe déjà")

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
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )