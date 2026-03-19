from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


# 🔒 Enum pour éviter erreurs de status
class BronzeStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class BronzeDocument(BaseModel):
    filename: str
    content_type: str  # application/pdf, image/jpeg, etc.
    file_data: str     # base64

    file_size: int
    sha256_hash: str

    # 🔥 IMPORTANT pour ton projet
    dossierId: int
    entrepriseId: int

    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    status: BronzeStatus = BronzeStatus.pending


class BronzeResponse(BaseModel):
    id: str

    filename: str
    sha256_hash: str

    dossierId: int
    entrepriseId: int

    uploaded_at: datetime
    status: BronzeStatus