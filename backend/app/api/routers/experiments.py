from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentGenerateRequest, ExperimentOut, ExperimentRunRequest
from app.services import posthog_events
from app.services.ai_features import generate_experiment
from app.services.analytics import compute_dashboard_metrics
from app.services.experiment_engine import run_experiment_simulation

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return list(
        db.scalars(
            select(Experiment)
            .where(Experiment.company_id == company_id)
            .order_by(Experiment.created_at.desc())
        )
    )


@router.post("/generate", response_model=ExperimentOut)
def generate(request: ExperimentGenerateRequest, db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    result = generate_experiment(db, company_id, request.focus_area)
    experiment = Experiment(company_id=company_id, **result)
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    posthog_events.track_experiment_created(company_id, experiment.id, experiment.hypothesis)
    return experiment


@router.post("/{experiment_id}/run", response_model=ExperimentOut)
def run(experiment_id: int, request: ExperimentRunRequest, db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    experiment = db.get(Experiment, experiment_id)
    if experiment is None or experiment.company_id != company_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    baseline_conversion_rate = compute_dashboard_metrics(db, company_id)["paid_conversion_rate"]
    result = run_experiment_simulation(
        baseline_conversion_rate=baseline_conversion_rate,
        expected_uplift_pct=float(experiment.expected_uplift_pct),
        sample_size_per_arm=request.sample_size_per_arm,
    )

    experiment.result_sample_size_per_arm = result["sample_size_per_arm"]
    experiment.result_control_conversions = result["control_conversions"]
    experiment.result_control_rate = result["control_rate"]
    experiment.result_variant_conversions = result["variant_conversions"]
    experiment.result_variant_rate = result["variant_rate"]
    experiment.result_observed_uplift_pct = result["observed_uplift_pct"]
    experiment.result_p_value = result["p_value"]
    experiment.result_is_significant = result["is_significant"]
    experiment.result_ci_low = result["confidence_interval_low"]
    experiment.result_ci_high = result["confidence_interval_high"]
    experiment.status = "completed"
    experiment.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(experiment)

    posthog_events.track_experiment_completed(
        company_id, experiment.id, result["is_significant"], result["observed_uplift_pct"]
    )
    return experiment
