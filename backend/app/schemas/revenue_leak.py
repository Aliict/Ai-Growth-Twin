from datetime import datetime

from pydantic import BaseModel


class RevenueLeakOut(BaseModel):
    id: int
    title: str
    stage: str
    description: str
    category: str
    monthly_impact: float
    status: str
    detected_at: datetime

    class Config:
        from_attributes = True


class RevenueLeakSummary(BaseModel):
    total_monthly_leakage: float
    leaks: list[RevenueLeakOut]
