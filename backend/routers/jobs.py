from datetime import date, datetime, time as dt_time

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_applicant, get_current_company
from database import get_db
from models import Application, Applicant, Company, JobPosting, JobType
from recruitment_webhook import fire_public_apply_webhook
from schemas import CompanyBrief, JobCreate, JobListOut, JobOut, RecruitmentApplyBody

router = APIRouter()


def _strip(s: str | None) -> str:
    return (s or "").strip()


def _build_description(body: JobCreate) -> str:
    if _strip(body.description):
        return _strip(body.description)
    # Structured role fields are stored separately; avoid duplicating them in description.
    if _strip(body.job_summary_purpose) or _strip(body.key_responsibilities) or _strip(body.team_context):
        return "—"
    return "See the full job posting for details."


def _date_to_dt(d: date | None, *, end_of_day: bool = False) -> datetime | None:
    if d is None:
        return None
    if end_of_day:
        return datetime.combine(d, dt_time(23, 59, 59))
    return datetime.combine(d, dt_time.min)


def _opt_str(s: str | None) -> str | None:
    t = _strip(s)
    return t if t else None


@router.get("/companies", response_model=list[CompanyBrief])
def list_companies_brief(db: Session = Depends(get_db)):
    rows = db.query(Company).order_by(Company.name.asc()).all()
    return [
        CompanyBrief(id=c.id, name=c.name, location=c.location, logo_path=c.logo_path)
        for c in rows
    ]


def job_to_out(
    job: JobPosting,
    db: Session,
    application_count: int | None = None,
) -> JobOut:
    company = db.query(Company).filter(Company.id == job.company_id).first()
    return JobOut(
        id=job.id,
        company_id=job.company_id,
        job_role=job.job_role,
        job_type=job.job_type,
        location=job.location,
        description=job.description,
        skills_required=job.skills_required,
        created_at=job.created_at,
        is_active=job.is_active,
        company_name=company.name if company else None,
        company_location=company.location if company else None,
        company_logo=company.logo_path if company else None,
        application_count=application_count,
        department_team=job.department_team,
        job_level_grade=job.job_level_grade,
        employment_type=job.employment_type,
        work_mode=job.work_mode,
        number_of_openings=job.number_of_openings if job.number_of_openings is not None else 1,
        job_code_requisition_id=job.job_code_requisition_id,
        job_summary_purpose=job.job_summary_purpose,
        key_responsibilities=job.key_responsibilities,
        team_context=job.team_context,
        min_education=job.min_education,
        years_experience_required=job.years_experience_required,
        required_skills_tools=job.required_skills_tools,
        preferred_skills_nice_to_have=job.preferred_skills_nice_to_have,
        salary_range_band=job.salary_range_band,
        stock_esop_details=job.stock_esop_details,
        benefits_summary=job.benefits_summary,
        application_deadline=job.application_deadline,
        expected_joining_date=job.expected_joining_date,
        posting_company_name=job.posting_company_name,
        company_description_mission=job.company_description_mission,
        culture_values=job.culture_values,
    )


@router.get("", response_model=JobListOut)
def list_jobs(
    company: str | None = None,
    job_type: str | None = None,
    sort_by: str = Query("date_desc", pattern="^(date_asc|date_desc)$"),
    date_from: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(JobPosting).filter(JobPosting.is_active == True)

    if company:
        q = q.join(Company, JobPosting.company_id == Company.id).filter(
            Company.name.ilike(f"%{company.strip()}%")
        )
    if job_type:
        try:
            jt = JobType(job_type)
            q = q.filter(JobPosting.job_type == jt)
        except ValueError:
            pass

    if date_from:
        try:
            dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            q = q.filter(JobPosting.created_at >= dt)
        except ValueError:
            pass

    if sort_by == "date_asc":
        q = q.order_by(JobPosting.created_at.asc())
    else:
        q = q.order_by(JobPosting.created_at.desc())

    items_db = q.all()
    items = [job_to_out(j, db) for j in items_db]
    return JobListOut(items=items, total=len(items))


@router.get("/mine", response_model=JobListOut)
def list_my_company_jobs(
    q: str | None = None,
    job_type: str | None = None,
    status: str = Query("all", pattern="^(all|active|inactive)$"),
    sort_by: str = Query("date_desc", pattern="^(date_asc|date_desc)$"),
    date_from: str | None = None,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    query = db.query(JobPosting).filter(JobPosting.company_id == company.id)

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                JobPosting.job_role.ilike(term),
                JobPosting.location.ilike(term),
                JobPosting.skills_required.ilike(term),
                JobPosting.department_team.ilike(term),
                JobPosting.job_code_requisition_id.ilike(term),
                JobPosting.required_skills_tools.ilike(term),
            )
        )
    if job_type:
        try:
            jt = JobType(job_type)
            query = query.filter(JobPosting.job_type == jt)
        except ValueError:
            pass
    if status == "active":
        query = query.filter(JobPosting.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(JobPosting.is_active.is_(False))

    if date_from:
        try:
            dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(JobPosting.created_at >= dt)
        except ValueError:
            pass

    if sort_by == "date_asc":
        query = query.order_by(JobPosting.created_at.asc())
    else:
        query = query.order_by(JobPosting.created_at.desc())

    items_db = query.all()
    job_ids = [j.id for j in items_db]
    counts: dict[int, int] = {}
    if job_ids:
        rows = (
            db.query(Application.job_id, func.count(Application.id))
            .filter(Application.job_id.in_(job_ids))
            .group_by(Application.job_id)
            .all()
        )
        counts = {int(r[0]): int(r[1]) for r in rows}

    items = [job_to_out(j, db, application_count=counts.get(j.id, 0)) for j in items_db]
    return JobListOut(items=items, total=len(items))


@router.get(
    "/{job_id}",
    response_model=JobOut,
    summary="Get job posting details",
    description=(
        "Returns one job posting by numeric ID: role, type, location, description, skills, "
        "company name/location/logo, timestamps, and active flag. "
        "Public (no auth). Returns 404 if the ID does not exist."
    ),
)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_out(job, db)


@router.post("", response_model=JobOut)
def create_job(
    body: JobCreate,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    skills = _strip(body.skills_required) or _strip(body.required_skills_tools) or "—"
    n_open = body.number_of_openings if body.number_of_openings is not None else 1
    job = JobPosting(
        company_id=company.id,
        job_role=body.job_role.strip(),
        job_type=body.job_type,
        location=body.location.strip(),
        description=_build_description(body),
        skills_required=skills,
        department_team=_opt_str(body.department_team),
        job_level_grade=_opt_str(body.job_level_grade),
        employment_type=_opt_str(body.employment_type),
        work_mode=_opt_str(body.work_mode),
        number_of_openings=n_open,
        job_code_requisition_id=_opt_str(body.job_code_requisition_id),
        job_summary_purpose=_opt_str(body.job_summary_purpose),
        key_responsibilities=_opt_str(body.key_responsibilities),
        team_context=_opt_str(body.team_context),
        min_education=_opt_str(body.min_education),
        years_experience_required=_opt_str(body.years_experience_required),
        required_skills_tools=_opt_str(body.required_skills_tools),
        preferred_skills_nice_to_have=_opt_str(body.preferred_skills_nice_to_have),
        salary_range_band=_opt_str(body.salary_range_band),
        stock_esop_details=_opt_str(body.stock_esop_details),
        benefits_summary=_opt_str(body.benefits_summary),
        application_deadline=_date_to_dt(body.application_deadline, end_of_day=True),
        expected_joining_date=_date_to_dt(body.expected_joining_date, end_of_day=False),
        posting_company_name=_opt_str(body.posting_company_name),
        company_description_mission=_opt_str(body.company_description_mission),
        culture_values=_opt_str(body.culture_values),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job_to_out(job, db)


@router.post("/{job_id}/apply")
def apply_job(
    job_id: int,
    body: RecruitmentApplyBody = Body(default_factory=RecruitmentApplyBody),
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id, JobPosting.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (
        db.query(Application)
        .filter(Application.job_id == job_id, Application.applicant_id == applicant.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already applied to this job")

    app = Application(job_id=job_id, applicant_id=applicant.id)
    db.add(app)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already applied to this job") from None
    db.refresh(app)

    pw = _strip(body.password) or None
    external_applicant_id = fire_public_apply_webhook(job, applicant, pw)
    if external_applicant_id:
        app.recruitment_external_applicant_id = external_applicant_id
        db.add(app)
        db.commit()
        db.refresh(app)

    return {
        "ok": True,
        "application_id": app.id,
        "recruitment_external_applicant_id": app.recruitment_external_applicant_id,
    }
