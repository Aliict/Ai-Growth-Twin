"""Regression coverage for a real bug found during manual testing: seed data
that let 'trial usage' happen without 'team invite' first produced a
negative dropoff_rate (more users reaching a later stage than an earlier
one). The funnel is defined as strictly sequential, so every stage's
reached-count must be <= the previous stage's.
"""

import pytest

from app.services.analytics import compute_dashboard_metrics, compute_funnel
from tests.conftest import make_trial_user


def _seed_realistic_funnel(db_session, company_id):
    users = []
    # 10 users who only sign up
    for i in range(10):
        users.append(make_trial_user(company_id, email=f"signup{i}@example.com"))
    # 8 who activate but go no further
    for i in range(8):
        users.append(make_trial_user(company_id, email=f"activated{i}@example.com", activated=True))
    # 5 who reach project creation
    for i in range(5):
        users.append(
            make_trial_user(
                company_id, email=f"project{i}@example.com", activated=True, project_created=True
            )
        )
    # 3 who reach team invite
    for i in range(3):
        users.append(
            make_trial_user(
                company_id,
                email=f"invited{i}@example.com",
                activated=True,
                project_created=True,
                team_invited=True,
            )
        )
    # 2 who use the trial and convert (paying, active)
    for i in range(2):
        users.append(
            make_trial_user(
                company_id,
                email=f"paid{i}@example.com",
                activated=True,
                project_created=True,
                team_invited=True,
                trial_usage=True,
                converted=True,
                plan="pro",
                mrr=79.0,
            )
        )
    db_session.add_all(users)
    db_session.commit()
    return users


def test_funnel_stages_are_monotonically_non_increasing(db_session, company):
    _seed_realistic_funnel(db_session, company.id)
    stages = compute_funnel(db_session, company.id)

    previous_users = None
    for stage in stages:
        if previous_users is not None:
            assert stage["users"] <= previous_users
        assert stage["dropoff_rate"] >= 0, f"negative dropoff at {stage['stage']} indicates a non-sequential funnel"
        assert stage["revenue_impact"] >= 0
        previous_users = stage["users"]


def test_funnel_stage_counts_match_seeded_data(db_session, company):
    _seed_realistic_funnel(db_session, company.id)
    stages = {s["stage"]: s for s in compute_funnel(db_session, company.id)}

    total = 10 + 8 + 5 + 3 + 2
    assert stages["signup"]["users"] == total
    assert stages["activation"]["users"] == 8 + 5 + 3 + 2
    assert stages["project_creation"]["users"] == 5 + 3 + 2
    assert stages["team_invite"]["users"] == 3 + 2
    assert stages["trial_usage"]["users"] == 2
    assert stages["paid"]["users"] == 2


def test_dashboard_metrics_reflect_seeded_conversions(db_session, company):
    _seed_realistic_funnel(db_session, company.id)
    metrics = compute_dashboard_metrics(db_session, company.id)

    total = 10 + 8 + 5 + 3 + 2
    assert metrics["trial_users"] == total
    assert metrics["paid_conversion_rate"] == pytest.approx(2 / total, abs=1e-4)
    assert metrics["mrr"] == pytest.approx(2 * 79.0)
    assert metrics["arr"] == pytest.approx(metrics["mrr"] * 12)
