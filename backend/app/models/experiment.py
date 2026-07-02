from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Experiment(Base):
    """An experiment starts as an LLM-generated hypothesis (status="suggested").

    Calling POST /api/experiments/{id}/run simulates a randomized
    control/variant trial against it (see app/services/experiment_engine.py)
    and fills in the result_* columns below, moving status to "completed".
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    hypothesis: Mapped[str] = mapped_column(Text)
    current_variant: Mapped[str] = mapped_column(Text)
    suggested_variant: Mapped[str] = mapped_column(Text)
    expected_uplift_pct: Mapped[float] = mapped_column(Numeric(5, 2))
    expected_revenue_impact: Mapped[float] = mapped_column(Numeric(10, 2))
    confidence_score: Mapped[float] = mapped_column(Numeric(3, 2))
    status: Mapped[str] = mapped_column(String(50), default="suggested")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    result_sample_size_per_arm: Mapped[int | None] = mapped_column(Integer, default=None)
    result_control_conversions: Mapped[int | None] = mapped_column(Integer, default=None)
    result_control_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), default=None)
    result_variant_conversions: Mapped[int | None] = mapped_column(Integer, default=None)
    result_variant_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), default=None)
    result_observed_uplift_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), default=None)
    result_p_value: Mapped[float | None] = mapped_column(Numeric(6, 4), default=None)
    result_is_significant: Mapped[bool | None] = mapped_column(default=None)
    result_ci_low: Mapped[float | None] = mapped_column(Numeric(6, 4), default=None)
    result_ci_high: Mapped[float | None] = mapped_column(Numeric(6, 4), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
