from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.schemas.dashboard import ExecutiveDashboard
from app.services.analytics import compute_dashboard_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=ExecutiveDashboard)
def get_dashboard(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return compute_dashboard_metrics(db, company_id)
