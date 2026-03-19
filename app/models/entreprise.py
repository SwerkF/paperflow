from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EntrepriseDocument(BaseModel):
    siret: Optional[str] = None
    siren: Optional[str] = None
    denomination_sociale: Optional[str] = None
    forme_juridique: Optional[str] = None
    adresse_siege: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EntrepriseCreate(BaseModel):
    siret: Optional[str] = None
    siren: Optional[str] = None
    denomination_sociale: Optional[str] = None


class EntrepriseResponse(BaseModel):
    id: str
    siret: Optional[str] = None
    siren: Optional[str] = None
    denomination_sociale: Optional[str] = None
    forme_juridique: Optional[str] = None
    adresse_siege: Optional[str] = None
    created_at: datetime
    updated_at: datetime