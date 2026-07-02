from datetime import datetime

from pydantic import BaseModel


class RoadmapItemOut(BaseModel):
    id: int
    quarter: str
    title: str
    description: str
    revenue_impact: float
    effort: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class RoadmapGenerateRequest(BaseModel):
    quarter: str
