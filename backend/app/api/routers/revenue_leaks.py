from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.models.revenue_leak import RevenueLeak
from app.schemas.revenue_leak import RevenueLeakSummary
from app.services.ai_features import detect_revenue_leaks

router = APIRouter(prefix="/api/revenue-leaks", tags=["revenue-leaks"])


@router.get("", response_model=RevenueLeakSummary)
def list_revenue_leaks(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    leaks = list(
        db.scalars(select(RevenueLeak).where(RevenueLeak.company_id == company_id))
    )
    total = sum(float(leak.monthly_impact) for leak in leaks)
    return {"total_monthly_leakage": round(total, 2), "leaks": leaks}


@router.post("/detect", response_model=RevenueLeakSummary)
def detect(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    leaks = detect_revenue_leaks(db, company_id)
    total = sum(float(leak.monthly_impact) for leak in leaks)
    return {"total_monthly_leakage": round(total, 2), "leaks": leaks}
