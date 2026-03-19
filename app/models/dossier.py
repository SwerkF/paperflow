from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DossierDocument(BaseModel):
    external_id: int
    entreprise_id: str

    nom: str
    type: Optional[str] = None
    status: str = "open"
    description: Optional[str] = None

    created_by: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DossierCreate(BaseModel):
    external_id: int
    entreprise_id: str
    nom: str
    created_by: str


class DossierResponse(BaseModel):
    id: str
    external_id: int
    entreprise_id: str
    nom: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime