from pydantic import BaseModel


class FunnelStage(BaseModel):
    stage: str
    users: int
    conversion_rate: float
    dropoff_rate: float
    revenue_impact: float


class FunnelAnalysis(BaseModel):
    stages: list[FunnelStage]
    overall_conversion_rate: float
