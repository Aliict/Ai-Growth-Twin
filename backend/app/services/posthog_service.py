from datetime import datetime

import posthog

from app.core.config import get_settings

settings = get_settings()

posthog.api_key = settings.posthog_api_key
posthog.host = settings.posthog_host
posthog.disabled = not settings.posthog_api_key


def is_enabled() -> bool:
    return not posthog.disabled


def capture(
    distinct_id: str,
    event: str,
    properties: dict | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Send an event to PostHog. No-ops safely when POSTHOG_API_KEY is unset.

    `timestamp` lets seed data backfill historical events (e.g. a signup
    from 40 days ago) instead of everything landing "now" in PostHog.
    """
    posthog.capture(
        distinct_id=distinct_id,
        event=event,
        properties=properties or {},
        timestamp=timestamp,
    )
