from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401 registers models on Base.metadata
from app.core.database import Base
from app.models.company import Company
from app.models.trial_user import TrialUser

NOW = datetime(2026, 6, 1, 12, 0, 0)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture()
def company(db_session):
    c = Company(name="Test Co", plan="growth")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def make_trial_user(
    company_id: int,
    *,
    email: str = "user@example.com",
    channel: str = "organic",
    signup_days_ago: float = 30,
    activated: bool = False,
    project_created: bool = False,
    team_invited: bool = False,
    trial_usage: bool = False,
    converted: bool = False,
    churned: bool = False,
    plan: str | None = None,
    mrr: float = 0.0,
    days_to_convert: float = 5,
    days_to_churn: float = 20,
    reference_now: datetime = NOW,
) -> TrialUser:
    """Build a TrialUser with an internally-consistent, strictly sequential
    funnel journey (signup -> activation -> project -> team invite -> trial
    usage -> paid), matching the funnel's assumed stage ordering.

    `reference_now` anchors `signup_days_ago`; pass `datetime.utcnow()` when
    testing code that itself measures elapsed time against the real clock
    (e.g. growth_analytics' retention curve), otherwise the fixed default
    keeps tests deterministic regardless of when they're run.
    """
    signup_at = reference_now - timedelta(days=signup_days_ago)
    activated_at = signup_at + timedelta(hours=2) if activated else None
    project_created_at = activated_at + timedelta(hours=2) if activated and project_created else None
    team_invited_at = (
        project_created_at + timedelta(hours=2) if project_created and team_invited else None
    )
    last_active_at = team_invited_at + timedelta(hours=2) if team_invited and trial_usage else None
    converted_at = last_active_at + timedelta(days=days_to_convert) if trial_usage and converted else None
    churned_at = converted_at + timedelta(days=days_to_churn) if converted and churned else None

    return TrialUser(
        company_id=company_id,
        email=email,
        channel=channel,
        signup_at=signup_at,
        activated_at=activated_at,
        project_created_at=project_created_at,
        team_invited_at=team_invited_at,
        last_active_at=last_active_at,
        converted_at=converted_at,
        churned_at=churned_at,
        plan=plan,
        mrr=mrr,
    )
