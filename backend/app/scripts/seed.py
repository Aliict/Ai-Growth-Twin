"""Seed demo data for a single company.

Assumes the schema already exists (run `alembic upgrade head` first).

Usage: python -m app.scripts.seed
"""

import random
from datetime import datetime, timedelta, timezone

from app import models  # noqa: F401  (registers models on Base.metadata)
from app.core.database import SessionLocal
from app.core.pricing import CHANNEL_PROFILES, PLAN_PRICES
from app.models.company import Company
from app.models.trial_user import TrialUser

random.seed(42)

TOTAL_TRIAL_USERS = 500
NOW = datetime.now(timezone.utc)

CHANNELS = list(CHANNEL_PROFILES.keys())
CHANNEL_WEIGHTS = [CHANNEL_PROFILES[c]["weight"] for c in CHANNELS]

# Channel quality multipliers applied to the baseline activation/conversion
# probabilities below — referrals and content convert better than cold paid
# search traffic, which is the realistic pattern this dataset is meant to
# make visible in the channel breakdown.
CHANNEL_ACTIVATION_MULTIPLIER = {
    "organic": 1.0,
    "referral": 1.2,
    "content": 1.1,
    "paid_search": 0.85,
}
CHANNEL_CONVERSION_MULTIPLIER = {
    "organic": 1.0,
    "referral": 1.3,
    "content": 1.05,
    "paid_search": 0.75,
}


def _days_ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


def seed() -> None:
    db = SessionLocal()
    try:
        db.query(TrialUser).delete()
        db.query(Company).delete()
        db.commit()

        company = Company(name="Acme SaaS Inc.", plan="growth")
        db.add(company)
        db.commit()
        db.refresh(company)

        users = []
        for i in range(TOTAL_TRIAL_USERS):
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]

            signup_days_ago = random.uniform(1, 90)
            signup_at = _days_ago(signup_days_ago)

            activated = random.random() < 0.55 * CHANNEL_ACTIVATION_MULTIPLIER[channel]
            activated_at = signup_at + timedelta(hours=random.uniform(0.5, 48)) if activated else None

            project_created = activated and random.random() < 0.75
            project_created_at = (
                activated_at + timedelta(hours=random.uniform(0.1, 24)) if project_created else None
            )

            team_invited = project_created and random.random() < 0.6
            team_invited_at = (
                project_created_at + timedelta(days=random.uniform(0.1, 5)) if team_invited else None
            )

            last_active = team_invited and random.random() < 0.8
            last_active_at = (
                team_invited_at + timedelta(days=random.uniform(0.5, 10)) if last_active else None
            )

            converted = last_active and random.random() < 0.36 * CHANNEL_CONVERSION_MULTIPLIER[channel]
            converted_at = (
                last_active_at + timedelta(days=random.uniform(0.5, 7)) if converted else None
            )

            churned_at = None
            mrr = 0.0
            plan = None
            if converted:
                plan = random.choice(["starter", "pro", "pro", "business"])
                mrr = PLAN_PRICES[plan]
                if random.random() < 0.08:
                    churned_at = converted_at + timedelta(days=random.uniform(10, 60))

            users.append(
                TrialUser(
                    company_id=company.id,
                    email=f"user{i}@example.com",
                    channel=channel,
                    signup_at=signup_at,
                    activated_at=activated_at,
                    project_created_at=project_created_at,
                    team_invited_at=team_invited_at,
                    last_active_at=last_active_at,
                    converted_at=converted_at,
                    churned_at=churned_at,
                    mrr=mrr,
                    plan=plan,
                )
            )

        db.add_all(users)
        db.commit()
        print(f"Seeded company '{company.name}' (id={company.id}) with {len(users)} trial users.")

        from app.services.posthog_events import backfill_historical_events

        backfill_historical_events(company.id, users)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
