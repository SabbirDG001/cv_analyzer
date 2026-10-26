import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import SkillSource, Track

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    aliases: list[str]


class ProfileIn(BaseModel):
    name: ShortText
    university: ShortText
    year: int = Field(ge=1, le=8)
    department: ShortText
    cgpa: Decimal = Field(ge=0, le=4, max_digits=3, decimal_places=2)
    track: Track
    field_id: int


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consent_at: datetime | None


class SkillLevelIn(BaseModel):
    level: int = Field(ge=0, le=5)


class ProfileSkillOut(BaseModel):
    skill_id: int
    name: str
    level: int
    source: SkillSource
