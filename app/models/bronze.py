from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BronzeDocument(BaseModel):
    filename: str                          # nom du fichier original
    content_type: str                      # "application/pdf" ou "image/jpeg"
    file_data: str                         # fichier encodé en base64
    file_size: int                         # taille en octets
    sha256_hash: str                       # empreinte pour détecter les doublons
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"               # pending → processing → done

class BronzeResponse(BaseModel):
    id: str
    filename: str
    sha256_hash: str
    uploaded_at: datetime
    status: str