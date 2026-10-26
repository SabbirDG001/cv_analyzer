from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.db.session import get_db
from app.models import Profile
from app.schemas.api import ProfileIn, ProfileOut, ProfileSkillOut, SkillLevelIn
from app.services import profile as service

router = APIRouter(prefix="/me", tags=["me"])


def _require_profile(db: Session, user: AuthUser) -> None:
    if service.get_profile(db, user.id) is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Complete onboarding first")


@router.get("/profile", response_model=ProfileOut)
def read_profile(
    user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> Profile:
    profile = service.get_profile(db, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    return profile


@router.put("/profile", response_model=ProfileOut)
def save_profile(
    body: ProfileIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    try:
        return service.upsert_profile(db, user.id, body)
    except service.UnknownReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown {exc}") from exc


@router.get("/skills", response_model=list[ProfileSkillOut])
def read_skills(
    user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ProfileSkillOut]:
    return service.list_profile_skills(db, user.id)


@router.put("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def save_skill(
    skill_id: int,
    body: SkillLevelIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _require_profile(db, user)
    try:
        service.set_skill_level(db, user.id, skill_id, body.level)
    except service.UnknownReferenceError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if not service.remove_skill(db, user.id, skill_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not in profile")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
