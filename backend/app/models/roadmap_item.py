from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RoadmapItem(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    quarter: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    revenue_impact: Mapped[float] = mapped_column(Numeric(10, 2))
    effort: Mapped[str] = mapped_column(String(20))
    confidence_score: Mapped[float] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
