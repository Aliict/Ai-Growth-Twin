from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrialUser(Base):
    """A single user's journey through the trial funnel.

    Stage timestamps are nullable and set in order as the user progresses:
    signup -> activation -> project_created -> team_invited -> paid.
    A null timestamp means the user has not (yet) reached that stage.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    email: Mapped[str] = mapped_column(String(255))

    signup_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    activated_at: Mapped[datetime | None] = mapped_column(default=None)
    project_created_at: Mapped[datetime | None] = mapped_column(default=None)
    team_invited_at: Mapped[datetime | None] = mapped_column(default=None)
    last_active_at: Mapped[datetime | None] = mapped_column(default=None)
    converted_at: Mapped[datetime | None] = mapped_column(default=None)
    churned_at: Mapped[datetime | None] = mapped_column(default=None)

    mrr: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    plan: Mapped[str | None] = mapped_column(String(50), default=None)
    channel: Mapped[str] = mapped_column(String(50), default="organic")
