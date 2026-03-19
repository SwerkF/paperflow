from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class SilverDocument(BaseModel):
    bronze_id: str
    filename: str

    document_type: Optional[str] = None  # facture, devis, etc.
    ocr_text: Optional[str] = None

    extracted_fields: Dict[str, Any] = Field(default_factory=dict)

    ocr_confidence: Optional[float] = None

    processed_at: datetime = Field(default_factory=datetime.utcnow)

    status: str = "pending"  # pending → processed → verified → error


class SilverResponse(BaseModel):
    id: str
    bronze_id: str

    document_type: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)

    status: str