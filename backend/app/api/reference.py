from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Field
from app.schemas.api import FieldOut, SkillOut
from app.services.profile import search_skills

router = APIRouter(tags=["reference"])


@router.get("/fields", response_model=list[FieldOut])
def list_fields(db: Session = Depends(get_db)) -> list[Field]:
    return list(db.scalars(select(Field).order_by(Field.name)))


@router.get("/skills", response_model=list[SkillOut])
def list_skills(q: str = Query("", max_length=80), db: Session = Depends(get_db)) -> list[SkillOut]:
    return [SkillOut.model_validate(s) for s in search_skills(db, q)]
