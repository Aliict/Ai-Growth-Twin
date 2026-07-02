from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RevenueLeak(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    title: Mapped[str] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="onboarding_friction")
    monthly_impact: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(50), default="open")
    detected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
