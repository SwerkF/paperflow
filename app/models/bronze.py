from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class BronzeStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"

class DocumentType(str, Enum):
    facture = "facture"
    devis = "devis"
    kbis = "kbis"
    rib = "rib"
    attestation_urssaf = "attestation_urssaf"
    attestation_vigilance = "attestation_vigilance"
    contrat = "contrat"
    autre = "autre"

class BronzeDocument(BaseModel):
    filename: str
    content_type: str
    file_data: str
    file_size: int
    sha256_hash: str
    dossierId: int
    entrepriseId: int
    document_type: DocumentType = DocumentType.autre  # ← nouveau
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: BronzeStatus = BronzeStatus.pending

class BronzeResponse(BaseModel):
    id: str
    filename: str
    sha256_hash: str
    dossierId: int
    entrepriseId: int
    document_type: DocumentType  # ← nouveau
    uploaded_at: datetime
    status: BronzeStatus