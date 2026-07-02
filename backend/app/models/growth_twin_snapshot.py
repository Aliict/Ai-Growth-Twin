from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GrowthTwinSnapshot(Base):
    """A point-in-time prediction of the business produced by the Growth Twin Engine.

    predicted_mrr / churn / activation / conversion are derived from real
    sklearn models trained on this company's TrialUser history (see
    app/services/ml_engine.py) rather than fixed heuristics. The *_model_auc
    and *_feature_importance fields expose that model's own self-reported
    quality so the prediction isn't presented as more certain than it is.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    predicted_mrr: Mapped[float] = mapped_column(Numeric(10, 2))
    predicted_churn_rate: Mapped[float] = mapped_column(Numeric(5, 4))
    predicted_activation_rate: Mapped[float] = mapped_column(Numeric(5, 4))
    predicted_expansion_mrr: Mapped[float] = mapped_column(Numeric(10, 2))
    predicted_paid_conversion_rate: Mapped[float] = mapped_column(Numeric(5, 4))

    conversion_model_auc: Mapped[float | None] = mapped_column(Numeric(5, 4), default=None)
    conversion_model_accuracy: Mapped[float | None] = mapped_column(Numeric(5, 4), default=None)
    churn_model_auc: Mapped[float | None] = mapped_column(Numeric(5, 4), default=None)
    churn_model_accuracy: Mapped[float | None] = mapped_column(Numeric(5, 4), default=None)
    conversion_feature_importance: Mapped[dict] = mapped_column(JSON, default=dict)
    churn_feature_importance: Mapped[dict] = mapped_column(JSON, default=dict)
    insufficient_data: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
