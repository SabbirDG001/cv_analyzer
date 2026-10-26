import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Field, Profile, ProfileSkill, Skill, SkillSource
from app.schemas.api import ProfileIn, ProfileSkillOut


class UnknownReferenceError(ValueError):
    """Raised when a request points at a field or skill that does not exist."""


def get_profile(db: Session, user_id: uuid.UUID) -> Profile | None:
    return db.get(Profile, user_id)


def upsert_profile(db: Session, user_id: uuid.UUID, data: ProfileIn) -> Profile:
    if db.get(Field, data.field_id) is None:
        raise UnknownReferenceError("field_id")
    profile = db.get(Profile, user_id)
    if profile is None:
        profile = Profile(id=user_id)
        db.add(profile)
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    return profile


def list_profile_skills(db: Session, user_id: uuid.UUID) -> list[ProfileSkillOut]:
    rows = db.execute(
        select(ProfileSkill, Skill.name)
        .join(Skill, Skill.id == ProfileSkill.skill_id)
        .where(ProfileSkill.profile_id == user_id)
        .order_by(Skill.name)
    ).all()
    return [
        ProfileSkillOut(skill_id=ps.skill_id, name=name, level=ps.level, source=ps.source)
        for ps, name in rows
    ]


def set_skill_level(db: Session, user_id: uuid.UUID, skill_id: int, level: int) -> None:
    if db.get(Skill, skill_id) is None:
        raise UnknownReferenceError("skill_id")
    stmt = insert(ProfileSkill).values(
        profile_id=user_id, skill_id=skill_id, level=level, source=SkillSource.MANUAL
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["profile_id", "skill_id"],
        set_={"level": level, "source": SkillSource.MANUAL},
    )
    db.execute(stmt)
    db.commit()


def remove_skill(db: Session, user_id: uuid.UUID, skill_id: int) -> bool:
    row = db.get(ProfileSkill, (user_id, skill_id))
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def search_skills(db: Session, query: str, limit: int = 20) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.name).limit(limit)
    if query.strip():
        pattern = f"%{query.strip()}%"
        haystack = Skill.name + " " + func.array_to_string(Skill.aliases, " ")
        stmt = stmt.where(haystack.ilike(pattern))
    return list(db.scalars(stmt))
