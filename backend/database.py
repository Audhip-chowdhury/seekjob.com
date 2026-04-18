import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'seekjob.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def migrate_sqlite_job_posting_columns() -> None:
    """Add columns when upgrading an existing SQLite DB (create_all does not alter tables)."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "job_postings" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("job_postings")}
    alters = [
        ("department_team", "VARCHAR(255)"),
        ("job_level_grade", "VARCHAR(128)"),
        ("employment_type", "VARCHAR(64)"),
        ("work_mode", "VARCHAR(64)"),
        ("number_of_openings", "INTEGER DEFAULT 1"),
        ("job_code_requisition_id", "VARCHAR(128)"),
        ("job_summary_purpose", "TEXT"),
        ("key_responsibilities", "TEXT"),
        ("team_context", "TEXT"),
        ("min_education", "VARCHAR(255)"),
        ("years_experience_required", "VARCHAR(128)"),
        ("required_skills_tools", "TEXT"),
        ("preferred_skills_nice_to_have", "TEXT"),
        ("salary_range_band", "TEXT"),
        ("stock_esop_details", "TEXT"),
        ("benefits_summary", "TEXT"),
        ("application_deadline", "DATETIME"),
        ("expected_joining_date", "DATETIME"),
        ("posting_company_name", "VARCHAR(255)"),
        ("company_description_mission", "TEXT"),
        ("culture_values", "TEXT"),
    ]
    with engine.begin() as conn:
        for col, ddl in alters:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE job_postings ADD COLUMN {col} {ddl}"))


def migrate_sqlite_application_columns() -> None:
    """Add columns when upgrading an existing SQLite applications table."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "applications" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("applications")}
    if "recruitment_external_applicant_id" not in existing:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE applications ADD COLUMN recruitment_external_applicant_id VARCHAR(255)"
                )
            )


def migrate_sqlite_recruitment_inbound_offers() -> None:
    """Create recruitment_inbound_offers table on legacy SQLite DBs if missing."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "recruitment_inbound_offers" in insp.get_table_names():
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE recruitment_inbound_offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_offer_id VARCHAR(36) NOT NULL UNIQUE,
                    application_id INTEGER REFERENCES applications(id),
                    applicant_id INTEGER REFERENCES applicants(id),
                    job_id INTEGER REFERENCES job_postings(id),
                    external_company_id VARCHAR(36) NOT NULL,
                    external_application_id VARCHAR(36),
                    recruitment_external_applicant_id VARCHAR(64) NOT NULL,
                    job_posting_code VARCHAR(16),
                    start_date VARCHAR(32),
                    external_offer_status VARCHAR(64) NOT NULL,
                    sent_at DATETIME,
                    compensation_json TEXT NOT NULL,
                    event_type VARCHAR(64) NOT NULL DEFAULT 'offer.created',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_rinbound_ext_applicant "
                "ON recruitment_inbound_offers (recruitment_external_applicant_id)"
            )
        )


def migrate_sqlite_recruitment_inbound_offer_response_columns() -> None:
    """Add applicant response columns on existing SQLite recruitment_inbound_offers tables."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "recruitment_inbound_offers" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("recruitment_inbound_offers")}
    with engine.begin() as conn:
        if "applicant_response_status" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE recruitment_inbound_offers "
                    "ADD COLUMN applicant_response_status VARCHAR(32)"
                )
            )
        if "applicant_responded_at" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE recruitment_inbound_offers ADD COLUMN applicant_responded_at DATETIME"
                )
            )


def migrate_sqlite_application_unique_job_applicant() -> None:
    """One application per (job, applicant); adds unique index on existing SQLite DBs."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "applications" not in insp.get_table_names():
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_applications_job_applicant "
                "ON applications (job_id, applicant_id)"
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
