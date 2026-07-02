from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.schemas.simulator import SimulationRequest, SimulationResult
from app.services.analytics import simulate

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.post("", response_model=SimulationResult)
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return simulate(
        db,
        company_id,
        request.activation_rate_delta_pct,
        request.paid_conversion_rate_delta_pct,
        request.churn_rate_delta_pct,
    )
