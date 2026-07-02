from datetime import datetime

from pydantic import BaseModel


class AdvisorAskRequest(BaseModel):
    question: str


class AdvisorMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdvisorAskResponse(BaseModel):
    answer: str
    sources: list[str]
    history: list[AdvisorMessageOut]
