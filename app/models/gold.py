from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class IncohérenceDetail(BaseModel):
    type: str           # ex: "SIRET_MISMATCH", "DATE_EXPIRÉE"
    description: str    # ex: "SIRET facture ≠ SIRET attestation"
    severity: str       # "low", "medium", "high"

class GoldDocument(BaseModel):
    silver_id: str                              # référence Silver
    bronze_id: str                              # référence Bronze
    filename: str
    document_type: str
    validated_fields: dict = {}                 # champs nettoyés et validés
    coherence_score: float = 1.0               # 0.0 à 1.0
    incoherences: List[IncohérenceDetail] = [] # liste des anomalies détectées
    is_fraudulent: bool = False
    curated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "valid"                       # valid / warning / rejected

class GoldResponse(BaseModel):
    id: str
    silver_id: str
    document_type: str
    coherence_score: float
    incoherences: list
    is_fraudulent: bool
    status: str