"""
Mark demo applicants as hired in SeekJob (pipeline status).

Targets applicants with emails appl1–appl4 @email.com (lowercase in DB). Updates every
application row for each applicant to status ``hired`` (same convention as the
HworkR recruitment status webhook).

Run from ``seekjob.com/backend``::

    python seed_applicants_hired.py

Idempotent: already-hired rows are left unchanged. Uses ``seekjob.db`` via ``database.SessionLocal``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Applicant, Application

TARGET_EMAILS = (
    "appl1@email.com",
    "appl2@email.com",
    "appl3@email.com",
    "appl4@email.com",
)

HIRED_STATUS = "hired"


def run(session: Session) -> None:
    missing: list[str] = []
    no_applications: list[str] = []
    updated_rows = 0

    for email in TARGET_EMAILS:
        applicant = session.query(Applicant).filter(Applicant.email == email).first()
        if applicant is None:
            missing.append(email)
            continue
        apps = (
            session.query(Application)
            .filter(Application.applicant_id == applicant.id)
            .all()
        )
        if not apps:
            no_applications.append(email)
            continue
        for app in apps:
            if app.status != HIRED_STATUS:
                app.status = HIRED_STATUS
                app.updated_at = datetime.utcnow()
                updated_rows += 1

    session.commit()

    print(f"Set status={HIRED_STATUS!r} on {updated_rows} application row(s).")
    if missing:
        print("No applicant row for email(s):", ", ".join(missing))
    if no_applications:
        print("Applicant exists but no application row(s):", ", ".join(no_applications))


def main() -> None:
    db = SessionLocal()
    try:
        run(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
