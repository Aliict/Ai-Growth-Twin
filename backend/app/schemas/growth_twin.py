from datetime import datetime

from pydantic import BaseModel


class GrowthTwinSnapshotOut(BaseModel):
    id: int
    predicted_mrr: float
    predicted_churn_rate: float
    predicted_activation_rate: float
    predicted_expansion_mrr: float
    predicted_paid_conversion_rate: float
    conversion_model_auc: float | None
    conversion_model_accuracy: float | None
    churn_model_auc: float | None
    churn_model_accuracy: float | None
    conversion_feature_importance: dict[str, float]
    churn_feature_importance: dict[str, float]
    insufficient_data: bool
    created_at: datetime

    class Config:
        from_attributes = True
