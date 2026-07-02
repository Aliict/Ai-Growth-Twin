from datetime import datetime, timedelta

from app.services.growth_analytics import (
    compute_retention_curve,
    compute_signup_cohorts,
    forecast_revenue,
)
from tests.conftest import NOW, make_trial_user


def test_signup_cohorts_groups_by_month(db_session, company):
    users = [
        make_trial_user(
            company.id,
            email="june@example.com",
            signup_days_ago=0,
            activated=True,
            project_created=True,
            team_invited=True,
            trial_usage=True,
            converted=True,
            plan="pro",
            mrr=79.0,
        ),
        make_trial_user(company.id, email="april@example.com", signup_days_ago=35),
    ]
    db_session.add_all(users)
    db_session.commit()

    cohorts = {row["cohort"]: row for row in compute_signup_cohorts(db_session, company.id)}

    june_key = NOW.strftime("%Y-%m")
    april_key = (NOW - timedelta(days=35)).strftime("%Y-%m")

    assert cohorts[june_key]["signups"] == 1
    assert cohorts[june_key]["converted"] == 1
    assert cohorts[april_key]["signups"] == 1
    assert cohorts[april_key]["converted"] == 0


def test_retention_curve_reflects_churn_timing(db_session, company):
    real_now = datetime.utcnow()

    still_active = make_trial_user(
        company.id,
        email="loyal@example.com",
        reference_now=real_now,
        signup_days_ago=250,
        activated=True,
        project_created=True,
        team_invited=True,
        trial_usage=True,
        converted=True,
        days_to_convert=1,
        plan="pro",
        mrr=79.0,
    )
    early_churn = make_trial_user(
        company.id,
        email="early_churn@example.com",
        reference_now=real_now,
        signup_days_ago=250,
        activated=True,
        project_created=True,
        team_invited=True,
        trial_usage=True,
        converted=True,
        churned=True,
        days_to_convert=1,
        days_to_churn=10,
        plan="starter",
        mrr=29.0,
    )
    db_session.add_all([still_active, early_churn])
    db_session.commit()

    curve = {p["month"]: p for p in compute_retention_curve(db_session, company.id, max_months=3)}

    for month in range(4):
        assert curve[month]["eligible_customers"] == 2

    assert curve[0]["retained_pct"] == 1.0
    # early_churn churned 10 days after converting, so by the month-1 (30 day) mark it's gone
    assert curve[1]["retained_pct"] == 0.5


def test_forecast_shows_positive_trend_when_mrr_is_growing(db_session, company):
    real_now = datetime.utcnow()
    users = []
    for weeks_ago in [10, 8, 6, 4, 2]:
        users.append(
            make_trial_user(
                company.id,
                email=f"cust{weeks_ago}@example.com",
                reference_now=real_now,
                signup_days_ago=weeks_ago * 7 + 5,
                activated=True,
                project_created=True,
                team_invited=True,
                trial_usage=True,
                converted=True,
                days_to_convert=1,
                plan="pro",
                mrr=79.0,
            )
        )
    db_session.add_all(users)
    db_session.commit()

    forecast = forecast_revenue(db_session, company.id, weeks_history=12, weeks_ahead=4)

    assert forecast["trend_per_week"] > 0
    assert len(forecast["forecast"]) == 4
    assert forecast["forecast"][-1]["predicted_mrr"] >= forecast["history"][-1]["mrr"]
