from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.models import AnswerTrace
from backend.app.db.session import get_db

router = APIRouter()


def _require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    if x_admin_key != settings.admin_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.get("/admin/traces")
async def list_traces(
    limit: int = 50,
    offset: int = 0,
    db: Annotated[Session, Depends(get_db)] = None,
    _: Annotated[None, Depends(_require_admin)] = None,
) -> dict[str, Any]:
    total = db.query(AnswerTrace).count()
    rows = db.query(AnswerTrace).order_by(AnswerTrace.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": r.id,
                "question_hash": r.question_hash,
                "question_redacted": r.question_redacted,
                "valid": r.valid,
                "pii_types": r.pii_types_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
