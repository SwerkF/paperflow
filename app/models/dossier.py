from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DossierDocument(BaseModel):
    entreprise_id: str

    nom: str
    type: Optional[str] = None
    status: str = "open"
    description: Optional[str] = None

    created_by: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DossierCreate(BaseModel):
    entreprise_id: str
    nom: str
    created_by: str


class DossierResponse(BaseModel):
    id: str
    entreprise_id: str
    nom: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime