from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=400)]


class ParsedSkill(BaseModel):
    name: Text
    level: int = Field(ge=0, le=5, description="Estimated 0-5 proficiency")
    evidence: Text = Field(description="One line from the CV supporting the level")


class ParsedEducation(BaseModel):
    institution: Text
    degree: Text = ""
    period: Text = ""


class ParsedProject(BaseModel):
    title: Text
    summary: Text = ""


class ParsedExperience(BaseModel):
    role: Text
    organization: Text = ""
    summary: Text = ""


class ParsedTestScore(BaseModel):
    test: Text
    score: Text


class ParsedCv(BaseModel):
    education: list[ParsedEducation] = []
    cgpa: float | None = Field(default=None, ge=0, le=4)
    skills: list[ParsedSkill] = []
    projects: list[ParsedProject] = []
    experience: list[ParsedExperience] = []
    languages: list[Text] = []
    test_scores: list[ParsedTestScore] = []
    interests: list[Text] = []


class MatchedSkill(BaseModel):
    skill_id: int
    name: str
    level: int
    evidence: str


class UnmatchedSkill(BaseModel):
    name: str
    level: int
    evidence: str


class CvReview(BaseModel):
    cv_id: str
    parsed: ParsedCv
    matched: list[MatchedSkill]
    unmatched: list[UnmatchedSkill]


class ConfirmedSkill(BaseModel):
    skill_id: int
    level: int = Field(ge=0, le=5)


class CvConfirmIn(BaseModel):
    skills: list[ConfirmedSkill] = Field(max_length=200)
