from pydantic import BaseModel


class ExecutiveDashboard(BaseModel):
    mrr: float
    arr: float
    trial_users: int
    activation_rate: float
    paid_conversion_rate: float
    revenue_leakage: float
    expansion_opportunity: float
    arpu: float
    ltv: float
    cac: float | None
    payback_period_months: float | None
    ltv_cac_ratio: float | None
