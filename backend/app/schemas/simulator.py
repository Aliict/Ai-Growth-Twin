from pydantic import BaseModel


class SimulationRequest(BaseModel):
    activation_rate_delta_pct: float = 0
    paid_conversion_rate_delta_pct: float = 0
    churn_rate_delta_pct: float = 0


class SimulationResult(BaseModel):
    baseline_mrr: float
    projected_mrr: float
    mrr_delta: float
    baseline_activation_rate: float
    projected_activation_rate: float
    baseline_paid_conversion_rate: float
    projected_paid_conversion_rate: float
    baseline_churn_rate: float
    projected_churn_rate: float
