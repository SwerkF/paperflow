from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EntrepriseDocument(BaseModel):
    external_id: int
    siret: Optional[str] = None
    siren: Optional[str] = None

    denomination_sociale: Optional[str] = None
    forme_juridique: Optional[str] = None
    adresse_siege: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EntrepriseCreate(BaseModel):
    external_id: int
    siret: Optional[str] = None
    siren: Optional[str] = None
    denomination_sociale: Optional[str] = None


class EntrepriseResponse(BaseModel):
    id: str
    external_id: int
    siret: Optional[str]
    siren: Optional[str]
    denomination_sociale: Optional[str]
    forme_juridique: Optional[str]
    adresse_siege: Optional[str]
    created_at: datetime
    updated_at: datetime