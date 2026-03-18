from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SilverDocument(BaseModel):
    bronze_id: str                         # référence au document brut
    filename: str
    document_type: Optional[str] = None   # "facture", "devis", "kbis", "rib"...
    ocr_text: Optional[str] = None        # texte brut extrait par OCR
    extracted_fields: Optional[dict] = {} # SIRET, montant, date... extraits
    ocr_confidence: Optional[float] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"               # pending → verified → error

class SilverResponse(BaseModel):
    id: str
    bronze_id: str
    document_type: Optional[str]
    extracted_fields: Optional[dict]
    status: str