from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.models.roadmap_item import RoadmapItem
from app.schemas.roadmap import RoadmapGenerateRequest, RoadmapItemOut
from app.services.ai_features import generate_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


@router.get("", response_model=list[RoadmapItemOut])
def list_roadmap(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return list(
        db.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.company_id == company_id)
            .order_by(RoadmapItem.created_at.desc())
        )
    )


@router.post("/generate", response_model=list[RoadmapItemOut])
def generate(request: RoadmapGenerateRequest, db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return generate_roadmap(db, company_id, request.quarter)
