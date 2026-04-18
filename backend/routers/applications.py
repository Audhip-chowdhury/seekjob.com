import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_applicant, get_current_company
from database import get_db
from models import Application, Applicant, Company, JobPosting
from recruitment_matching import resolve_application_strict
from schemas import ApplicationOut, ApplicationStatusUpdate, RecruitmentStatusCallback

router = APIRouter()
logger = logging.getLogger(__name__)

# Canonical path for HworkR ``RECRUITMENT_STATUS_WEBHOOK_URL`` (e.g. http://127.0.0.1:8020/recruitment/application-status).
RECRUITMENT_STATUS_WEBHOOK_PATH = "/recruitment/application-status"


def _run_recruitment_status_webhook(
    body: RecruitmentStatusCallback,
    db: Session,
) -> ApplicationOut:
    """
    Inbound pipeline webhook: set ``Application.status`` from the external ``status`` string.

    Configure HworkR with ``RECRUITMENT_STATUS_WEBHOOK_URL`` pointing at
    ``POST {SeekJob base}{RECRUITMENT_STATUS_WEBHOOK_PATH}`` (default ``http://127.0.0.1:8020/recruitment/application-status``).
    """
    logger.info(
        "POST %s request body: %s",
        RECRUITMENT_STATUS_WEBHOOK_PATH,
        body.model_dump(mode="json"),
    )

    external_id = body.recruitment_external_applicant_id
    app = resolve_application_strict(
        db,
        external_id,
        body.job_posting_code,
        log_prefix=RECRUITMENT_STATUS_WEBHOOK_PATH,
    )

    logger.info(
        "%s: applicant_id=%s application_id=%s recruitment_external_applicant_id=%r job_posting_code=%r",
        RECRUITMENT_STATUS_WEBHOOK_PATH,
        app.applicant_id,
        app.id,
        external_id,
        body.job_posting_code,
    )
    print(
        f"[{RECRUITMENT_STATUS_WEBHOOK_PATH}] applicant_id:",
        app.applicant_id,
        "| application_id:",
        app.id,
        "| recruitment_external_applicant_id:",
        repr(external_id),
        "| job_posting_code:",
        repr(body.job_posting_code),
    )

    app.status = body.status
    app.updated_at = datetime.utcnow()
    db.add(app)
    db.commit()
    db.refresh(app)
    result = enrich_application(app, db, include_applicant_files=False)
    logger.info(
        "POST %s response body: %s",
        RECRUITMENT_STATUS_WEBHOOK_PATH,
        result.model_dump(mode="json"),
    )
    return result


@router.post(
    RECRUITMENT_STATUS_WEBHOOK_PATH,
    response_model=ApplicationOut,
    summary="Recruitment pipeline status webhook",
    description=(
        "Inbound JSON webhook from HworkR after pipeline updates. "
        "Fields: ``recruitment_external_applicant_id`` (candidate UUID), ``status`` (pipeline string), "
        "optional ``job_posting_code`` (matches posting ``job_code_requisition_id`` when multiple applications share the same external id)."
    ),
)
def recruitment_status_webhook(
    body: RecruitmentStatusCallback,
    db: Session = Depends(get_db),
):
    return _run_recruitment_status_webhook(body, db)


@router.post(
    "/recruitment/application_status",
    response_model=ApplicationOut,
    summary="Recruitment pipeline status webhook (legacy path)",
    description="Same as ``POST /recruitment/application-status``; kept for older clients.",
    include_in_schema=True,
)
def recruitment_status_webhook_legacy_path(
    body: RecruitmentStatusCallback,
    db: Session = Depends(get_db),
):
    return _run_recruitment_status_webhook(body, db)


def enrich_application(
    app: Application,
    db: Session,
    include_applicant_files: bool = False,
) -> ApplicationOut:
    job = db.query(JobPosting).filter(JobPosting.id == app.job_id).first()
    applicant = db.query(Applicant).filter(Applicant.id == app.applicant_id).first()
    company_name = None
    job_role = None
    if job:
        job_role = job.job_role
        c = db.query(Company).filter(Company.id == job.company_id).first()
        company_name = c.name if c else None
    pic = applicant.picture_path if applicant and include_applicant_files else None
    cv = applicant.cv_path if applicant and include_applicant_files else None
    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        applicant_id=app.applicant_id,
        status=app.status,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        recruitment_external_applicant_id=app.recruitment_external_applicant_id,
        job_role=job_role,
        company_name=company_name,
        applicant_name=applicant.name if applicant else None,
        applicant_email=applicant.email if applicant else None,
        applicant_picture_path=pic,
        applicant_cv_path=cv,
    )


@router.get("/applicant/applications", response_model=list[ApplicationOut])
def list_applicant_applications(
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    apps = (
        db.query(Application)
        .filter(Application.applicant_id == applicant.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return [enrich_application(a, db, include_applicant_files=False) for a in apps]


@router.get("/company/applications", response_model=list[ApplicationOut])
def list_company_applications(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    job_ids = [j.id for j in db.query(JobPosting).filter(JobPosting.company_id == company.id).all()]
    if not job_ids:
        return []
    apps = (
        db.query(Application)
        .filter(Application.job_id.in_(job_ids))
        .order_by(Application.applied_at.desc())
        .all()
    )
    return [enrich_application(a, db, include_applicant_files=True) for a in apps]


@router.patch("/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    body: ApplicationStatusUpdate,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.query(JobPosting).filter(JobPosting.id == app.job_id).first()
    if not job or job.company_id != company.id:
        raise HTTPException(status_code=403, detail="Not your job posting")

    app.status = body.status
    app.updated_at = datetime.utcnow()
    db.add(app)
    db.commit()
    db.refresh(app)
    return enrich_application(app, db, include_applicant_files=True)
