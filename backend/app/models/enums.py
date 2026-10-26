import enum


class Track(enum.StrEnum):
    JOB = "job"
    RESEARCH = "research"
    SCHOLARSHIP = "scholarship"


class SkillSource(enum.StrEnum):
    CV = "cv"
    MANUAL = "manual"
    QUIZ = "quiz"


class OpportunityOrigin(enum.StrEnum):
    SEED = "seed"
    GROUNDED = "grounded"


class CheckStage(enum.StrEnum):
    PRE = "pre"
    POST = "post"
