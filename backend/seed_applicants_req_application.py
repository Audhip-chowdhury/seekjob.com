"""

Seed four demo applicants and ensure each has an application on a given job.



Defaults: emails ``appl1`` … ``appl4`` @ ``email.com`` (stored lowercase like login),

job id **61**. Creates ``Applicant`` rows when missing (picture + CV under ``uploads/``),

then inserts ``Application`` rows if needed.



Run from ``seekjob.com/backend``::



    python seed_applicants_req_application.py

    python seed_applicants_req_application.py --job-id 61

    python seed_applicants_req_application.py --req-code E57GI7



Use ``--req-code`` to resolve the posting by ``job_code_requisition_id`` instead of ``--job-id``.



Idempotent for applications: skips existing (job_id, applicant_id). Uses ``seekjob.db``.

Demo password for newly created applicants: ``password123`` (same as ``seed.py``).

"""



from __future__ import annotations



import argparse

import os

import uuid

from datetime import datetime



from sqlalchemy.orm import Session



from auth import hash_password

from database import SessionLocal

from models import Applicant, Application, JobPosting

from recruitment_matching import normalize_job_posting_code

from seed import MINIMAL_JPEG, UPLOAD, ensure_upload_dirs, write_applicant_cv_pdf



TARGET_EMAILS = (

    "appl1@email.com",

    "appl2@email.com",

    "appl3@email.com",

    "appl4@email.com",

)



DEFAULT_JOB_ID = 61





def find_unique_job_for_req(session: Session, req_code: str) -> JobPosting:

    norm = normalize_job_posting_code(req_code)

    if not norm:

        raise SystemExit("req_code is empty after normalization")



    matched: list[JobPosting] = []

    for job in session.query(JobPosting).filter(JobPosting.job_code_requisition_id.isnot(None)).all():

        if normalize_job_posting_code(job.job_code_requisition_id) == norm:

            matched.append(job)



    if not matched:

        raise SystemExit(

            f"No job posting with job_code_requisition_id matching {norm!r}. "

            "Set Req on the listing in company dashboard (or DB) to match HworkR req_code."

        )

    if len(matched) > 1:

        ids = ", ".join(str(j.id) for j in matched)

        raise SystemExit(f"Multiple postings match {norm!r} (job ids: {ids}); fix duplicates first.")



    return matched[0]





def resolve_job(session: Session, job_id: int, req_code: str | None) -> JobPosting:

    if req_code and str(req_code).strip():

        return find_unique_job_for_req(session, req_code)

    job = session.query(JobPosting).filter(JobPosting.id == job_id).first()

    if job is None:

        raise SystemExit(f"No job posting with id={job_id}.")

    return job





def get_or_create_applicant(session: Session, email_raw: str, index_1_based: int) -> Applicant:

    email_norm = email_raw.strip().lower()

    existing = session.query(Applicant).filter(Applicant.email == email_norm).first()

    if existing is not None:

        return existing



    ensure_upload_dirs()

    pic_fname = f"seed_job61_{uuid.uuid4().hex}.jpg"

    pic_rel = f"pictures/{pic_fname}"

    with open(os.path.join(UPLOAD, pic_rel), "wb") as f:

        f.write(MINIMAL_JPEG)



    cv_rel = f"cvs/cv_seed_job61_{uuid.uuid4().hex}.pdf"

    cv_abs = os.path.join(UPLOAD, cv_rel)

    name = f"Demo Applicant {index_1_based}"

    write_applicant_cv_pdf(

        cv_abs,

        name,

        email_norm,

        "Seeded candidate for integration testing.",

        "General professional skills",

    )



    ap = Applicant(

        name=name,

        email=email_norm,

        password_hash=hash_password("password123"),

        picture_path=pic_rel,

        cv_path=cv_rel,

    )

    session.add(ap)

    session.flush()

    return ap





def run(session: Session, *, job_id: int, req_code: str | None) -> None:

    job = resolve_job(session, job_id, req_code)

    now = datetime.utcnow()



    applicants_created = 0

    apps_created = 0

    skipped_existing = 0



    for i, email in enumerate(TARGET_EMAILS, start=1):

        before = session.query(Applicant).filter(Applicant.email == email.strip().lower()).first()

        applicant = get_or_create_applicant(session, email, i)

        if before is None:

            applicants_created += 1



        existing = (

            session.query(Application)

            .filter(

                Application.job_id == job.id,

                Application.applicant_id == applicant.id,

            )

            .first()

        )

        if existing is not None:

            skipped_existing += 1

            continue



        session.add(

            Application(

                job_id=job.id,

                applicant_id=applicant.id,

                status="Applied",

                applied_at=now,

                updated_at=now,

            )

        )

        apps_created += 1



    session.commit()



    req = job.job_code_requisition_id or ""

    req_bit = f" req={req!r}" if req else ""

    print(

        f"job_id={job.id}{req_bit} ({job.job_role!r}). "

        f"Applicants created: {applicants_created}. "

        f"Applications created: {apps_created}, already applied (skipped): {skipped_existing}."

    )





def main() -> None:

    p = argparse.ArgumentParser(description="Seed demo applicants and applications for a SeekJob posting.")

    p.add_argument("--job-id", type=int, default=DEFAULT_JOB_ID, help=f"Job posting primary key (default: {DEFAULT_JOB_ID})")

    p.add_argument(

        "--req-code",

        default=None,

        help="If set, resolve posting by job_code_requisition_id instead of --job-id",

    )

    args = p.parse_args()



    db = SessionLocal()

    try:

        run(db, job_id=args.job_id, req_code=args.req_code)

    finally:

        db.close()





if __name__ == "__main__":

    main()


