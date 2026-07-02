"""Synthetic but internally-consistent SaaS pricing/channel assumptions.

These numbers are not observed from a real business — they're the fixed
"world model" the seed script and revenue calculations are built against, so
that MRR/ARR/LTV/CAC all derive from the same assumptions instead of each
metric inventing its own constant. Documented explicitly in the README.
"""

PLAN_PRICES: dict[str, float] = {
    "starter": 29.0,
    "pro": 79.0,
    "business": 199.0,
}

PLAN_ORDER = ["starter", "pro", "business"]

DEFAULT_ARPU = sum(PLAN_PRICES.values()) / len(PLAN_PRICES)

# Synthetic acquisition channels: relative share of trial signups, and an
# assumed fully-loaded cost per acquired trial signup (ad spend, content
# production cost amortized, referral incentive, etc). organic/referral are
# treated as ~free at the margin.
CHANNEL_PROFILES: dict[str, dict[str, float]] = {
    "organic": {"weight": 0.35, "cost_per_signup": 0.0},
    "paid_search": {"weight": 0.25, "cost_per_signup": 65.0},
    "content": {"weight": 0.20, "cost_per_signup": 22.0},
    "referral": {"weight": 0.20, "cost_per_signup": 8.0},
}

CHANNELS = list(CHANNEL_PROFILES.keys())

# Fallback assumption when there isn't enough churn history to estimate
# customer lifetime directly (avoids division by zero / absurd LTV).
MAX_ASSUMED_LIFETIME_MONTHS = 36.0
