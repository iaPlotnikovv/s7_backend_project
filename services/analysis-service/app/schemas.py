import uuid
from pydantic import BaseModel, ConfigDict



class AnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    profile_id: uuid.UUID
    cluster: int
    serialized_text: str
    x: float
    y: float

    