from sqlalchemy.orm import Session

from app.core.pricing import PLAN_PRICES
from app.services import revenue

FUNNEL_STAGES = [
    ("signup", "signup_at"),
    ("activation", "activated_at"),
    ("project_creation", "project_created_at"),
    ("team_invite", "team_invited_at"),
    ("trial_usage", "last_active_at"),
    ("paid", "converted_at"),
]


def _company_users(db: Session, company_id: int):
    return revenue.company_users(db, company_id)


def compute_funnel(db: Session, company_id: int) -> list[dict]:
    users = _company_users(db, company_id)
    total = len(users) or 1
    arpu = revenue.blended_arpu(revenue.active_paid_users(users))

    stages = []
    previous_count = total
    for stage_name, field in FUNNEL_STAGES:
        reached = sum(1 for u in users if getattr(u, field) is not None)
        conversion_rate = reached / total
        dropoff = previous_count - reached
        dropoff_rate = dropoff / previous_count if previous_count else 0
        revenue_impact = round(dropoff * arpu, 2)
        stages.append(
            {
                "stage": stage_name,
                "users": reached,
                "conversion_rate": round(conversion_rate, 4),
                "dropoff_rate": round(dropoff_rate, 4),
                "revenue_impact": revenue_impact,
            }
        )
        previous_count = reached

    return stages


def compute_dashboard_metrics(db: Session, company_id: int) -> dict:
    users = _company_users(db, company_id)
    total = len(users) or 1

    activated = sum(1 for u in users if u.activated_at is not None)
    converted = [u for u in users if u.converted_at is not None]
    active_paid = revenue.active_paid_users(users)

    mrr = float(sum(float(u.mrr) for u in active_paid))
    arr = mrr * 12
    activation_rate = activated / total
    paid_conversion_rate = len(converted) / total

    revenue_metrics = revenue.compute_revenue_metrics(db, company_id)
    arpu = revenue_metrics["arpu"]

    non_converted_activated = [
        u for u in users if u.activated_at is not None and u.converted_at is None
    ]
    revenue_leakage = round(len(non_converted_activated) * arpu, 2)

    # Expansion opportunity: entry-tier customers who could plausibly upgrade
    # to the next plan up, discounted by an assumed upsell-conversion rate.
    starter_plan_users = [u for u in active_paid if u.plan == "starter"]
    upgrade_delta = PLAN_PRICES["pro"] - PLAN_PRICES["starter"]
    expansion_opportunity = round(len(starter_plan_users) * upgrade_delta * 0.5, 2)

    return {
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "trial_users": total,
        "activation_rate": round(activation_rate, 4),
        "paid_conversion_rate": round(paid_conversion_rate, 4),
        "revenue_leakage": revenue_leakage,
        "expansion_opportunity": expansion_opportunity,
        "arpu": arpu,
        "ltv": revenue_metrics["ltv"],
        "cac": revenue_metrics["cac"],
        "payback_period_months": revenue_metrics["payback_period_months"],
        "ltv_cac_ratio": revenue_metrics["ltv_cac_ratio"],
    }


def simulate(
    db: Session,
    company_id: int,
    activation_rate_delta_pct: float,
    paid_conversion_rate_delta_pct: float,
    churn_rate_delta_pct: float,
) -> dict:
    metrics = compute_dashboard_metrics(db, company_id)
    users = _company_users(db, company_id)
    total = len(users) or 1
    converted = [u for u in users if u.converted_at is not None]
    active_paid = revenue.active_paid_users(users)
    baseline_churn_rate = revenue.monthly_churn_rate(users)
    arpu = metrics["arpu"]

    baseline_activation = metrics["activation_rate"]
    baseline_conversion = metrics["paid_conversion_rate"]
    baseline_mrr = metrics["mrr"]

    projected_activation = min(1.0, baseline_activation * (1 + activation_rate_delta_pct / 100))
    projected_conversion = min(1.0, baseline_conversion * (1 + paid_conversion_rate_delta_pct / 100))
    projected_churn = max(0.0, baseline_churn_rate * (1 + churn_rate_delta_pct / 100))

    activation_lift = (projected_activation - baseline_activation) * total
    conversion_lift = (projected_conversion - baseline_conversion) * total
    churn_impact = (baseline_churn_rate - projected_churn) * len(active_paid)

    projected_mrr = baseline_mrr + (activation_lift + conversion_lift + churn_impact) * arpu
    projected_mrr = max(0.0, round(projected_mrr, 2))

    return {
        "baseline_mrr": baseline_mrr,
        "projected_mrr": projected_mrr,
        "mrr_delta": round(projected_mrr - baseline_mrr, 2),
        "baseline_activation_rate": round(baseline_activation, 4),
        "projected_activation_rate": round(projected_activation, 4),
        "baseline_paid_conversion_rate": round(baseline_conversion, 4),
        "projected_paid_conversion_rate": round(projected_conversion, 4),
        "baseline_churn_rate": round(baseline_churn_rate, 4),
        "projected_churn_rate": round(projected_churn, 4),
    }
