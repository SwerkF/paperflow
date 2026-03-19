from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class BronzeStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"

class BronzeDocument(BaseModel):
    filename: str
    content_type: str
    file_data: str
    file_size: int
    sha256_hash: str
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