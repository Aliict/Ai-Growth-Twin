from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


def get_demo_company_id(db: Session) -> int:
    """Single-tenant demo mode: operate on the first seeded company.

    Multi-tenant auth is out of scope for this scaffold; swap this for a
    real auth dependency (e.g. resolving company_id from a JWT) later.
    """
    company_id = db.scalars(select(Company.id).order_by(Company.id).limit(1)).first()
    if company_id is None:
        raise HTTPException(status_code=404, detail="No company found. Run the seed script first.")
    return company_id
