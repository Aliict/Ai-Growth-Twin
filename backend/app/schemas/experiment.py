from datetime import datetime

from pydantic import BaseModel


class ExperimentOut(BaseModel):
    id: int
    hypothesis: str
    current_variant: str
    suggested_variant: str
    expected_uplift_pct: float
    expected_revenue_impact: float
    confidence_score: float
    status: str
    created_at: datetime

    result_sample_size_per_arm: int | None
    result_control_conversions: int | None
    result_control_rate: float | None
    result_variant_conversions: int | None
    result_variant_rate: float | None
    result_observed_uplift_pct: float | None
    result_p_value: float | None
    result_is_significant: bool | None
    result_ci_low: float | None
    result_ci_high: float | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class ExperimentGenerateRequest(BaseModel):
    focus_area: str | None = None


class ExperimentRunRequest(BaseModel):
    sample_size_per_arm: int = 1000
