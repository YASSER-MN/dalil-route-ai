from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.models import Feedback
from backend.app.db.session import get_db

router = APIRouter()


class FeedbackIn(BaseModel):
    trace_id: str
    rating: Literal["helpful", "wrong", "unsafe"]
    comment: str | None = None


class FeedbackOut(BaseModel):
    id: str


@router.post("/feedback", response_model=FeedbackOut)
async def submit_feedback(
    body: FeedbackIn,
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackOut:
    row = Feedback(
        trace_id=body.trace_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackOut(id=row.id)
