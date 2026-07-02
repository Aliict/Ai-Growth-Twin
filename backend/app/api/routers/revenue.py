from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.schemas.revenue import RevenueMetrics
from app.services.revenue import compute_revenue_metrics

router = APIRouter(prefix="/api/revenue", tags=["revenue"])


@router.get("/segments", response_model=RevenueMetrics)
def get_revenue_segments(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return compute_revenue_metrics(db, company_id)
