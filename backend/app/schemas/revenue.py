from pydantic import BaseModel


class PlanBreakdown(BaseModel):
    plan: str
    customers: int
    mrr: float
    arpu: float
    share_of_customers: float


class ChannelBreakdown(BaseModel):
    channel: str
    signups: int
    conversions: int
    conversion_rate: float
    mrr: float
    cac: float | None


class RevenueMetrics(BaseModel):
    arpu: float
    monthly_churn_rate: float
    customer_lifetime_months: float
    ltv: float
    cac: float | None
    payback_period_months: float | None
    ltv_cac_ratio: float | None
    plan_breakdown: list[PlanBreakdown]
    channel_breakdown: list[ChannelBreakdown]
