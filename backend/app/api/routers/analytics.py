from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.schemas.analytics import CohortRow, RetentionPoint, RevenueForecast
from app.services.growth_analytics import (
    compute_retention_curve,
    compute_signup_cohorts,
    forecast_revenue,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/cohorts", response_model=list[CohortRow])
def get_cohorts(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return compute_signup_cohorts(db, company_id)


@router.get("/retention", response_model=list[RetentionPoint])
def get_retention(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return compute_retention_curve(db, company_id)


@router.get("/forecast", response_model=RevenueForecast)
def get_forecast(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return forecast_revenue(db, company_id)
