from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum


class IncoherenceSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class GoldStatus(str, Enum):
    valid = "valid"
    warning = "warning"
    rejected = "rejected"


class IncoherenceDetail(BaseModel):
    type: str
    description: str
    severity: IncoherenceSeverity


class GoldDocument(BaseModel):
    silver_id: str
    bronze_id: str

    filename: str
    document_type: str

    validated_fields: Dict[str, Any] = Field(default_factory=dict)

    coherence_score: float = 1.0

    incoherences: List[IncoherenceDetail] = Field(default_factory=list)

    is_fraudulent: bool = False

    curated_at: datetime = Field(default_factory=datetime.utcnow)

    status: GoldStatus = GoldStatus.valid


class GoldResponse(BaseModel):
    id: str
    silver_id: str
    bronze_id: str

    document_type: str
    coherence_score: float

    incoherences: List[IncoherenceDetail] = Field(default_factory=list)

    is_fraudulent: bool
    status: GoldStatus