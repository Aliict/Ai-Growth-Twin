import pytest

from app.services import revenue
from tests.conftest import make_trial_user


def _seed_three_customers(db_session, company_id):
    users = [
        make_trial_user(
            company_id,
            email="pro@example.com",
            channel="organic",
            activated=True,
            project_created=True,
            team_invited=True,
            trial_usage=True,
            converted=True,
            plan="pro",
            mrr=79.0,
        ),
        make_trial_user(
            company_id,
            email="business@example.com",
            channel="organic",
            activated=True,
            project_created=True,
            team_invited=True,
            trial_usage=True,
            converted=True,
            plan="business",
            mrr=199.0,
        ),
        make_trial_user(
            company_id,
            email="churned@example.com",
            channel="paid_search",
            activated=True,
            project_created=True,
            team_invited=True,
            trial_usage=True,
            converted=True,
            churned=True,
            plan="starter",
            mrr=29.0,
        ),
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


def test_blended_arpu_is_revenue_weighted_not_flat_constant(db_session, company):
    _seed_three_customers(db_session, company.id)
    users = revenue.company_users(db_session, company.id)
    active_paid = revenue.active_paid_users(users)

    assert len(active_paid) == 2  # the churned starter customer is excluded
    assert revenue.blended_arpu(active_paid) == pytest.approx((79.0 + 199.0) / 2)


def test_blended_arpu_falls_back_to_default_when_no_paying_customers(db_session, company):
    assert revenue.blended_arpu([]) == pytest.approx(revenue.DEFAULT_ARPU)


def test_monthly_churn_rate_and_lifetime(db_session, company):
    _seed_three_customers(db_session, company.id)
    users = revenue.company_users(db_session, company.id)

    churn_rate = revenue.monthly_churn_rate(users)
    assert churn_rate == pytest.approx(1 / 3)

    lifetime = revenue.customer_lifetime_months(churn_rate)
    assert lifetime == pytest.approx(1 / churn_rate)


def test_customer_lifetime_caps_at_max_when_churn_is_zero(db_session, company):
    lifetime = revenue.customer_lifetime_months(0.0)
    assert lifetime == revenue.MAX_ASSUMED_LIFETIME_MONTHS


def test_plan_breakdown_only_counts_active_paying_customers(db_session, company):
    _seed_three_customers(db_session, company.id)
    users = revenue.company_users(db_session, company.id)
    active_paid = revenue.active_paid_users(users)

    breakdown = {row["plan"]: row for row in revenue.plan_breakdown(active_paid)}
    assert set(breakdown) == {"pro", "business"}
    assert breakdown["pro"]["customers"] == 1
    assert breakdown["pro"]["arpu"] == pytest.approx(79.0)


def test_channel_breakdown_reflects_per_channel_cac_assumptions(db_session, company):
    _seed_three_customers(db_session, company.id)
    users = revenue.company_users(db_session, company.id)

    breakdown = {row["channel"]: row for row in revenue.channel_breakdown(users)}

    assert breakdown["organic"]["signups"] == 2
    assert breakdown["organic"]["conversions"] == 2
    assert breakdown["organic"]["cac"] == pytest.approx(0.0)  # organic cost_per_signup is 0

    assert breakdown["paid_search"]["signups"] == 1
    assert breakdown["paid_search"]["conversions"] == 1
    assert breakdown["paid_search"]["cac"] == pytest.approx(65.0)
    # the paid_search customer churned, so it shouldn't count toward active MRR
    assert breakdown["paid_search"]["mrr"] == pytest.approx(0.0)


def test_compute_revenue_metrics_is_internally_consistent(db_session, company):
    _seed_three_customers(db_session, company.id)
    metrics = revenue.compute_revenue_metrics(db_session, company.id)

    # Each field is independently rounded for display, so compare with an
    # absolute tolerance wide enough to absorb compounded rounding rather
    # than re-deriving exact float equality from already-rounded inputs.
    assert metrics["ltv"] == pytest.approx(metrics["arpu"] * metrics["customer_lifetime_months"], abs=0.5)
    if metrics["cac"]:
        assert metrics["payback_period_months"] == pytest.approx(metrics["cac"] / metrics["arpu"], abs=0.01)
        assert metrics["ltv_cac_ratio"] == pytest.approx(metrics["ltv"] / metrics["cac"], abs=0.05)
