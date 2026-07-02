from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pricing import CHANNEL_PROFILES, DEFAULT_ARPU, MAX_ASSUMED_LIFETIME_MONTHS
from app.models.trial_user import TrialUser


def company_users(db: Session, company_id: int) -> list[TrialUser]:
    return list(db.scalars(select(TrialUser).where(TrialUser.company_id == company_id)))


def active_paid_users(users: list[TrialUser]) -> list[TrialUser]:
    return [u for u in users if u.converted_at is not None and u.churned_at is None]


def blended_arpu(active_paid: list[TrialUser]) -> float:
    """Revenue-weighted average revenue per active paying user.

    Falls back to the average list price across plans when there isn't yet
    a paid base to compute a real blend from (e.g. a brand new company).
    """
    if not active_paid:
        return DEFAULT_ARPU
    total_mrr = sum(float(u.mrr) for u in active_paid)
    return total_mrr / len(active_paid)


def monthly_churn_rate(users: list[TrialUser]) -> float:
    converted = [u for u in users if u.converted_at is not None]
    if not converted:
        return 0.0
    churned = [u for u in converted if u.churned_at is not None]
    return len(churned) / len(converted)


def customer_lifetime_months(churn_rate: float) -> float:
    if churn_rate <= 0:
        return MAX_ASSUMED_LIFETIME_MONTHS
    return min(1 / churn_rate, MAX_ASSUMED_LIFETIME_MONTHS)


def plan_breakdown(active_paid: list[TrialUser]) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    mrr_by_plan: dict[str, float] = defaultdict(float)
    for u in active_paid:
        plan = u.plan or "unknown"
        counts[plan] += 1
        mrr_by_plan[plan] += float(u.mrr)

    total_customers = len(active_paid) or 1
    return [
        {
            "plan": plan,
            "customers": counts[plan],
            "mrr": round(mrr_by_plan[plan], 2),
            "arpu": round(mrr_by_plan[plan] / counts[plan], 2) if counts[plan] else 0.0,
            "share_of_customers": round(counts[plan] / total_customers, 4),
        }
        for plan in counts
    ]


def channel_breakdown(users: list[TrialUser]) -> list[dict]:
    """Per-channel signup volume, conversion rate, blended CAC, and MRR contribution."""
    by_channel: dict[str, list[TrialUser]] = defaultdict(list)
    for u in users:
        by_channel[u.channel or "organic"].append(u)

    rows = []
    for channel, channel_users in by_channel.items():
        converted = [u for u in channel_users if u.converted_at is not None]
        active_paid = active_paid_users(channel_users)
        cost_per_signup = CHANNEL_PROFILES.get(channel, {}).get("cost_per_signup", 0.0)
        total_spend = len(channel_users) * cost_per_signup
        cac = total_spend / len(converted) if converted else None
        rows.append(
            {
                "channel": channel,
                "signups": len(channel_users),
                "conversions": len(converted),
                "conversion_rate": round(len(converted) / len(channel_users), 4) if channel_users else 0.0,
                "mrr": round(sum(float(u.mrr) for u in active_paid), 2),
                "cac": round(cac, 2) if cac is not None else None,
            }
        )
    return sorted(rows, key=lambda r: r["mrr"], reverse=True)


def blended_cac(users: list[TrialUser]) -> float | None:
    """Total acquisition spend across all channels divided by total conversions."""
    total_spend = 0.0
    total_conversions = 0
    by_channel: dict[str, list[TrialUser]] = defaultdict(list)
    for u in users:
        by_channel[u.channel or "organic"].append(u)

    for channel, channel_users in by_channel.items():
        converted = [u for u in channel_users if u.converted_at is not None]
        cost_per_signup = CHANNEL_PROFILES.get(channel, {}).get("cost_per_signup", 0.0)
        total_spend += len(channel_users) * cost_per_signup
        total_conversions += len(converted)

    if total_conversions == 0:
        return None
    return total_spend / total_conversions


def compute_revenue_metrics(db: Session, company_id: int) -> dict:
    users = company_users(db, company_id)
    active_paid = active_paid_users(users)

    arpu = blended_arpu(active_paid)
    churn_rate = monthly_churn_rate(users)
    lifetime_months = customer_lifetime_months(churn_rate)
    ltv = round(arpu * lifetime_months, 2)

    cac = blended_cac(users)
    payback_period_months = round(cac / arpu, 2) if cac and arpu else None
    ltv_cac_ratio = round(ltv / cac, 2) if cac else None

    return {
        "arpu": round(arpu, 2),
        "monthly_churn_rate": round(churn_rate, 4),
        "customer_lifetime_months": round(lifetime_months, 2),
        "ltv": ltv,
        "cac": round(cac, 2) if cac is not None else None,
        "payback_period_months": payback_period_months,
        "ltv_cac_ratio": ltv_cac_ratio,
        "plan_breakdown": plan_breakdown(active_paid),
        "channel_breakdown": channel_breakdown(users),
    }
