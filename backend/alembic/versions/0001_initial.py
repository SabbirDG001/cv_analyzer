"""initial schema, enums and row level security

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ENUMS = {
    "track": ("job", "research", "scholarship"),
    "skill_source": ("cv", "manual", "quiz"),
    "opportunity_origin": ("seed", "grounded"),
    "check_stage": ("pre", "post"),
}

# Tables a user owns directly, keyed by their owner column.
OWNED_BY_PROFILE = ("profile_skills", "cv_uploads", "analyses", "learning_plans")
REFERENCE_TABLES = ("fields", "skills", "opportunities")


def _enum(name: str) -> pg.ENUM:
    return pg.ENUM(*ENUMS[name], name=name, create_type=False)


def _ensure_supabase_stubs() -> None:
    """On plain Postgres (local dev/tests) create the bits Supabase normally provides."""
    op.execute("""
        DO $$
        BEGIN
          IF to_regnamespace('auth') IS NULL THEN
            CREATE SCHEMA auth;
            CREATE TABLE auth.users (id uuid PRIMARY KEY);
            CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS
              $f$ SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $f$;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            CREATE ROLE authenticated NOLOGIN;
          END IF;
        END
        $$;
        """)
    op.execute("GRANT USAGE ON SCHEMA auth, public TO authenticated")
    op.execute("GRANT EXECUTE ON FUNCTION auth.uid() TO authenticated")


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def _create_tables() -> None:
    bind = op.get_bind()
    for name in ENUMS:
        _enum(name).create(bind, checkfirst=True)

    op.create_table(
        "fields",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("category", sa.String(80), nullable=False, server_default="general"),
        sa.Column("aliases", pg.ARRAY(sa.Text), nullable=False, server_default="{}"),
    )
    op.create_table(
        "profiles",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("university", sa.String(160), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("department", sa.String(160), nullable=False),
        sa.Column("cgpa", sa.Numeric(3, 2), nullable=False),
        sa.Column("track", _enum("track"), nullable=False),
        sa.Column("field_id", sa.Integer, sa.ForeignKey("fields.id"), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True)),
        _created_at(),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("year BETWEEN 1 AND 8", name="profiles_year_range"),
        sa.CheckConstraint("cgpa BETWEEN 0 AND 4", name="profiles_cgpa_range"),
    )
    op.create_table(
        "profile_skills",
        sa.Column(
            "profile_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("skill_id", sa.Integer, sa.ForeignKey("skills.id"), primary_key=True),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("source", _enum("skill_source"), nullable=False),
        sa.CheckConstraint("level BETWEEN 0 AND 5", name="profile_skills_level"),
    )
    op.create_table(
        "cv_uploads",
        _uuid_pk(),
        sa.Column(
            "profile_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("parsed_json", pg.JSONB),
        sa.Column("parsed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "opportunities",
        _uuid_pk(),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("org", sa.Text, nullable=False),
        sa.Column("person_name", sa.Text),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("field_id", sa.Integer, sa.ForeignKey("fields.id"), nullable=False),
        sa.Column("track", _enum("track"), nullable=False),
        sa.Column("location", sa.Text),
        sa.Column("required_skills", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin", _enum("opportunity_origin"), nullable=False),
    )
    op.create_table(
        "analyses",
        _uuid_pk(),
        sa.Column(
            "profile_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        _created_at(),
        sa.Column("match_results", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("gaps", pg.JSONB, nullable=False, server_default="[]"),
    )
    op.create_table(
        "skill_gaps",
        _uuid_pk(),
        sa.Column(
            "analysis_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.Integer, sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("priority_score", sa.Numeric(10, 4), nullable=False),
        sa.Column("unlocks_count", sa.Integer, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
    )
    op.create_table(
        "learning_plans",
        _uuid_pk(),
        sa.Column(
            "profile_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.Integer, sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("plan_json", pg.JSONB, nullable=False),
        _created_at(),
    )
    op.create_table(
        "practice_sessions",
        _uuid_pk(),
        sa.Column(
            "plan_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("learning_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hour_block", sa.Integer, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "self_checks",
        _uuid_pk(),
        sa.Column(
            "plan_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("learning_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", _enum("check_stage"), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("answers", pg.JSONB, nullable=False, server_default="[]"),
    )
    op.create_index("ix_profile_skills_skill", "profile_skills", ["skill_id"])
    op.create_index("ix_opportunities_field_track", "opportunities", ["field_id", "track"])


def _policy(table: str, using: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_owner ON {table} FOR ALL TO authenticated "
        f"USING ({using}) WITH CHECK ({using})"
    )


def _apply_rls() -> None:
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated"
    )
    _policy("profiles", "id = auth.uid()")
    for table in OWNED_BY_PROFILE:
        _policy(table, "profile_id = auth.uid()")
    _policy("skill_gaps", "analysis_id IN (SELECT id FROM analyses WHERE profile_id = auth.uid())")
    for table in ("practice_sessions", "self_checks"):
        _policy(table, "plan_id IN (SELECT id FROM learning_plans WHERE profile_id = auth.uid())")
    # Reference data is world-readable to signed-in users and never writable by them.
    for table in REFERENCE_TABLES:
        op.execute(f"REVOKE INSERT, UPDATE, DELETE ON {table} FROM authenticated")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_read ON {table} FOR SELECT TO authenticated USING (true)"
        )


def upgrade() -> None:
    _ensure_supabase_stubs()
    _create_tables()
    _apply_rls()


def downgrade() -> None:
    for table in (
        "self_checks",
        "practice_sessions",
        "learning_plans",
        "skill_gaps",
        "analyses",
        "opportunities",
        "cv_uploads",
        "profile_skills",
        "profiles",
        "skills",
        "fields",
    ):
        op.drop_table(table)
    for name in ENUMS:
        _enum(name).drop(op.get_bind(), checkfirst=True)
