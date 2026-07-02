from pydantic import BaseModel


class CohortRow(BaseModel):
    cohort: str
    signups: int
    converted: int
    conversion_rate: float
    still_active: int
    current_retention_rate: float | None


class RetentionPoint(BaseModel):
    month: int
    retained_pct: float | None
    eligible_customers: int


class MrrHistoryPoint(BaseModel):
    date: str
    mrr: float


class MrrForecastPoint(BaseModel):
    date: str
    predicted_mrr: float
    confidence_low: float
    confidence_high: float


class RevenueForecast(BaseModel):
    history: list[MrrHistoryPoint]
    forecast: list[MrrForecastPoint]
    trend_per_week: float
    r_squared: float | None
