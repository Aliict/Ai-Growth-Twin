from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.company import Company
from app.services.growth_twin_engine import generate_snapshot


@celery_app.task(name="app.tasks.growth_twin_tasks.refresh_growth_twin_snapshot")
def refresh_growth_twin_snapshot() -> int:
    """Recompute a Growth Twin snapshot for every company. Returns count of snapshots created."""
    db = SessionLocal()
    try:
        company_ids = db.scalars(select(Company.id)).all()
        for company_id in company_ids:
            generate_snapshot(db, company_id)
        return len(company_ids)
    finally:
        db.close()
