from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_demo_company_id
from app.core.database import get_db
from app.models.advisor_message import AdvisorMessage
from app.schemas.advisor import AdvisorAskRequest, AdvisorAskResponse, AdvisorMessageOut
from app.services.ai_features import ask_advisor

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


@router.post("/ask", response_model=AdvisorAskResponse)
def ask(request: AdvisorAskRequest, db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    result = ask_advisor(db, company_id, request.question)
    history = list(
        db.scalars(
            select(AdvisorMessage)
            .where(AdvisorMessage.company_id == company_id)
            .order_by(AdvisorMessage.created_at)
        )
    )
    return {"answer": result["answer"], "sources": result["sources"], "history": history}


@router.get("/history", response_model=list[AdvisorMessageOut])
def get_history(db: Session = Depends(get_db)):
    company_id = get_demo_company_id(db)
    return list(
        db.scalars(
            select(AdvisorMessage)
            .where(AdvisorMessage.company_id == company_id)
            .order_by(AdvisorMessage.created_at)
        )
    )
