import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CheckStage, OpportunityOrigin, SkillSource, Track


def _enum(enum_cls: type, name: str) -> Enum:
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(80), default="general")
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)


class Profile(Base):
    """One row per Supabase user; id is the auth.users id."""

    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1 AND 8", name="profiles_year_range"),
        CheckConstraint("cgpa BETWEEN 0 AND 4", name="profiles_cgpa_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    university: Mapped[str] = mapped_column(String(160))
    year: Mapped[int] = mapped_column(Integer)
    department: Mapped[str] = mapped_column(String(160))
    cgpa: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    track: Mapped[Track] = mapped_column(_enum(Track, "track"))
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProfileSkill(Base):
    __tablename__ = "profile_skills"
    __table_args__ = (CheckConstraint("level BETWEEN 0 AND 5", name="profile_skills_level"),)

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    level: Mapped[int] = mapped_column(Integer)
    source: Mapped[SkillSource] = mapped_column(_enum(SkillSource, "skill_source"))


class CvUpload(Base):
    __tablename__ = "cv_uploads"

    id: Mapped[uuid.UUID] = _uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    storage_path: Mapped[str] = mapped_column(Text)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = _uuid_pk()
    title: Mapped[str] = mapped_column(Text)
    org: Mapped[str] = mapped_column(Text)
    person_name: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(60))
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"))
    track: Mapped[Track] = mapped_column(_enum(Track, "track"))
    location: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    origin: Mapped[OpportunityOrigin] = mapped_column(
        _enum(OpportunityOrigin, "opportunity_origin")
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = _created_at()
    match_results: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    gaps: Mapped[list[Any]] = mapped_column(JSONB, default=list)


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id: Mapped[uuid.UUID] = _uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    priority_score: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    unlocks_count: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[uuid.UUID] = _uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created_at()


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_plans.id", ondelete="CASCADE"))
    hour_block: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class SelfCheck(Base):
    __tablename__ = "self_checks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_plans.id", ondelete="CASCADE"))
    stage: Mapped[CheckStage] = mapped_column(_enum(CheckStage, "check_stage"))
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    answers: Mapped[list[Any]] = mapped_column(JSONB, default=list)
