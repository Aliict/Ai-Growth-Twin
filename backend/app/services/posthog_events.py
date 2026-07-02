"""Named PostHog event helpers used across the app.

Every call site funnels through here so the event schema (names + property
shapes) lives in one place. All calls are safe no-ops when POSTHOG_API_KEY
is unset (see `posthog_service.capture`).
"""

from app.models.trial_user import TrialUser
from app.services import posthog_service


def _distinct_id(company_id: int, trial_user_id: int) -> str:
    return f"company-{company_id}-user-{trial_user_id}"


def track_signup(user: TrialUser) -> None:
    distinct_id = _distinct_id(user.company_id, user.id)
    posthog_service.capture(
        distinct_id,
        "user_signed_up",
        {"channel": user.channel, "email": user.email},
        timestamp=user.signup_at,
    )
    posthog_service.capture(
        distinct_id,
        "trial_started",
        {"channel": user.channel},
        timestamp=user.signup_at,
    )


def track_activation(user: TrialUser) -> None:
    if user.activated_at is None:
        return
    posthog_service.capture(
        _distinct_id(user.company_id, user.id),
        "user_activated",
        {"channel": user.channel},
        timestamp=user.activated_at,
    )


def track_funnel_stage(user: TrialUser, stage: str, at) -> None:
    if at is None:
        return
    posthog_service.capture(
        _distinct_id(user.company_id, user.id),
        "funnel_stage_changed",
        {"stage": stage, "channel": user.channel},
        timestamp=at,
    )


def track_conversion(user: TrialUser) -> None:
    if user.converted_at is None:
        return
    posthog_service.capture(
        _distinct_id(user.company_id, user.id),
        "subscription_started",
        {"plan": user.plan, "mrr": float(user.mrr), "channel": user.channel},
        timestamp=user.converted_at,
    )


def track_churn(user: TrialUser) -> None:
    if user.churned_at is None:
        return
    posthog_service.capture(
        _distinct_id(user.company_id, user.id),
        "churned",
        {"plan": user.plan, "mrr": float(user.mrr), "channel": user.channel},
        timestamp=user.churned_at,
    )


def track_experiment_created(company_id: int, experiment_id: int, hypothesis: str) -> None:
    posthog_service.capture(
        f"company-{company_id}",
        "experiment_created",
        {"experiment_id": experiment_id, "hypothesis": hypothesis},
    )


def track_experiment_completed(company_id: int, experiment_id: int, is_significant: bool, uplift_pct: float) -> None:
    posthog_service.capture(
        f"company-{company_id}",
        "experiment_completed",
        {
            "experiment_id": experiment_id,
            "is_significant": is_significant,
            "observed_uplift_pct": uplift_pct,
        },
    )


def backfill_historical_events(company_id: int, users: list[TrialUser]) -> None:
    """Replay every seeded user's funnel journey into PostHog with correct
    historical timestamps, so PostHog has a real (if synthetic) event history
    instead of only ever seeing "now"."""
    if not posthog_service.is_enabled():
        return

    for user in users:
        track_signup(user)
        track_activation(user)
        track_funnel_stage(user, "project_creation", user.project_created_at)
        track_funnel_stage(user, "team_invite", user.team_invited_at)
        track_funnel_stage(user, "trial_usage", user.last_active_at)
        track_conversion(user)
        track_churn(user)
