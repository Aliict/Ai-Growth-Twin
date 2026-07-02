import numpy as np
from sqlalchemy.orm import Session

from app.models.growth_twin_snapshot import GrowthTwinSnapshot
from app.services import ml_engine, revenue
from app.services.analytics import compute_dashboard_metrics


def generate_snapshot(db: Session, company_id: int) -> GrowthTwinSnapshot:
    """Predict next-period MRR/churn/conversion using sklearn models trained
    on this company's own trial-user history, instead of a fixed heuristic.

    - Conversion probability: RandomForestClassifier over funnel-stage flags,
      time-to-activate, and acquisition channel.
    - Churn probability: LogisticRegression over plan, MRR, time-to-convert,
      and channel, for currently active paying customers.

    Both models are retrained on every call (the dataset is small enough that
    this is instant) and their AUC/accuracy/feature importance are persisted
    alongside the prediction so the confidence of the forecast is visible,
    not just the forecast itself.
    """
    users = revenue.company_users(db, company_id)
    metrics = compute_dashboard_metrics(db, company_id)
    arpu = metrics["arpu"]

    converted_users = [u for u in users if u.converted_at is not None]
    active_paid = revenue.active_paid_users(users)
    in_flight = [u for u in users if u.converted_at is None]

    conversion_model = ml_engine.train_conversion_model(users)
    churn_model = ml_engine.train_churn_model(converted_users)

    if in_flight:
        conversion_probs = ml_engine.predict_conversion_probabilities(conversion_model, in_flight)
        expected_new_conversions = float(conversion_probs.sum())
    else:
        expected_new_conversions = 0.0

    total_users = len(users) or 1
    predicted_paid_conversion_rate = min(
        1.0, (len(converted_users) + expected_new_conversions) / total_users
    )

    if active_paid:
        churn_probs = ml_engine.predict_churn_probabilities(churn_model, active_paid)
        predicted_churn_rate = float(np.mean(churn_probs))
        expected_churned_mrr = float(sum(p * float(u.mrr) for p, u in zip(churn_probs, active_paid)))
    else:
        predicted_churn_rate = revenue.monthly_churn_rate(users)
        expected_churned_mrr = 0.0

    predicted_new_mrr = expected_new_conversions * arpu
    predicted_mrr = max(0.0, round(metrics["mrr"] + predicted_new_mrr - expected_churned_mrr, 2))

    snapshot = GrowthTwinSnapshot(
        company_id=company_id,
        predicted_mrr=predicted_mrr,
        predicted_churn_rate=round(predicted_churn_rate, 4),
        predicted_activation_rate=metrics["activation_rate"],
        predicted_expansion_mrr=metrics["expansion_opportunity"],
        predicted_paid_conversion_rate=round(predicted_paid_conversion_rate, 4),
        conversion_model_auc=conversion_model["auc"],
        conversion_model_accuracy=conversion_model["accuracy"],
        churn_model_auc=churn_model["auc"],
        churn_model_accuracy=churn_model["accuracy"],
        conversion_feature_importance=conversion_model["feature_importance"],
        churn_feature_importance=churn_model["feature_importance"],
        insufficient_data=conversion_model["insufficient_data"] or churn_model["insufficient_data"],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
