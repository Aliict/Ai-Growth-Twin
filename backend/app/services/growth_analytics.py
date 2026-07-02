"""Cohort retention, retention curves, and revenue forecasting.

Cohort/retention figures are computed directly from the seeded TrialUser
timestamps (real arithmetic over synthetic data, not further simulated).
Forecasting fits a small sklearn LinearRegression over the company's actual
historical weekly MRR trajectory (reconstructed from signup/convert/churn
dates) and projects forward with a residual-based confidence band.
"""

from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression

from app.services import revenue

WEEK = timedelta(days=7)


def compute_signup_cohorts(db, company_id: int) -> list[dict]:
    users = revenue.company_users(db, company_id)
    cohorts: dict[str, list] = defaultdict(list)
    for u in users:
        cohorts[u.signup_at.strftime("%Y-%m")].append(u)

    rows = []
    for cohort_key in sorted(cohorts):
        cohort_users = cohorts[cohort_key]
        converted = [u for u in cohort_users if u.converted_at is not None]
        active_paid = [u for u in converted if u.churned_at is None]
        rows.append(
            {
                "cohort": cohort_key,
                "signups": len(cohort_users),
                "converted": len(converted),
                "conversion_rate": round(len(converted) / len(cohort_users), 4) if cohort_users else 0.0,
                "still_active": len(active_paid),
                "current_retention_rate": round(len(active_paid) / len(converted), 4) if converted else None,
            }
        )
    return rows


def compute_retention_curve(db, company_id: int, max_months: int = 3) -> list[dict]:
    """% of paying customers still active N months after they converted."""
    users = revenue.company_users(db, company_id)
    converted = [u for u in users if u.converted_at is not None]
    now = datetime.utcnow()

    curve = []
    for month in range(max_months + 1):
        eligible = [u for u in converted if (now - u.converted_at).days >= month * 30]
        if not eligible:
            curve.append({"month": month, "retained_pct": None, "eligible_customers": 0})
            continue
        retained = [
            u
            for u in eligible
            if u.churned_at is None or (u.churned_at - u.converted_at).days > month * 30
        ]
        curve.append(
            {
                "month": month,
                "retained_pct": round(len(retained) / len(eligible), 4),
                "eligible_customers": len(eligible),
            }
        )
    return curve


def compute_mrr_history(db, company_id: int, weeks: int = 12) -> list[dict]:
    """Reconstruct actual weekly active-MRR from signup/convert/churn timestamps."""
    users = revenue.company_users(db, company_id)
    now = datetime.utcnow()
    start = now - timedelta(weeks=weeks)

    history = []
    for week_index in range(weeks + 1):
        as_of = start + week_index * WEEK
        if as_of > now:
            as_of = now
        active_mrr = sum(
            float(u.mrr)
            for u in users
            if u.converted_at is not None
            and u.converted_at <= as_of
            and (u.churned_at is None or u.churned_at > as_of)
        )
        history.append({"date": as_of.date().isoformat(), "mrr": round(active_mrr, 2)})

    return history


def forecast_revenue(db, company_id: int, weeks_history: int = 12, weeks_ahead: int = 8) -> dict:
    history = compute_mrr_history(db, company_id, weeks=weeks_history)

    X = np.arange(len(history)).reshape(-1, 1)
    y = np.array([point["mrr"] for point in history])

    model = LinearRegression()
    model.fit(X, y)

    residuals = y - model.predict(X)
    residual_std = float(np.std(residuals)) if len(residuals) > 1 else 0.0

    last_date = datetime.fromisoformat(history[-1]["date"])
    forecast = []
    for step in range(1, weeks_ahead + 1):
        x_future = len(history) - 1 + step
        predicted = float(model.predict([[x_future]])[0])
        predicted = max(0.0, predicted)
        # Uncertainty widens the further out the forecast goes.
        band = 1.96 * residual_std * (1 + step / weeks_ahead)
        forecast.append(
            {
                "date": (last_date + step * WEEK).date().isoformat(),
                "predicted_mrr": round(predicted, 2),
                "confidence_low": round(max(0.0, predicted - band), 2),
                "confidence_high": round(predicted + band, 2),
            }
        )

    return {
        "history": history,
        "forecast": forecast,
        "trend_per_week": round(float(model.coef_[0]), 2),
        "r_squared": round(float(model.score(X, y)), 4) if len(y) > 1 else None,
    }
