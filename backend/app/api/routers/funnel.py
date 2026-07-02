from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.schemas.funnel import FunnelAnalysis
from app.services.analytics import compute_funnel

router = APIRouter(prefix="/api/funnel", tags=["funnel"])


@router.get("", response_model=FunnelAnalysis)
def get_funnel(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    stages = compute_funnel(db, company_id)
    overall = stages[-1]["conversion_rate"] if stages else 0
    return {"stages": stages, "overall_conversion_rate": overall}
