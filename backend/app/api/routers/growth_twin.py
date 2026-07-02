from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.models.growth_twin_snapshot import GrowthTwinSnapshot
from app.schemas.growth_twin import GrowthTwinSnapshotOut
from app.services.growth_twin_engine import generate_snapshot

router = APIRouter(prefix="/api/growth-twin", tags=["growth-twin"])


@router.get("/snapshots", response_model=list[GrowthTwinSnapshotOut])
def list_snapshots(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return list(
        db.scalars(
            select(GrowthTwinSnapshot)
            .where(GrowthTwinSnapshot.company_id == company_id)
            .order_by(GrowthTwinSnapshot.created_at.desc())
            .limit(30)
        )
    )


@router.post("/refresh", response_model=GrowthTwinSnapshotOut)
def refresh(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return generate_snapshot(db, company_id)
