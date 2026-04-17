from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_applicant, get_current_company
from database import get_db
from models import Application, Applicant, Company, JobPosting, JobType
from schemas import CompanyBrief, JobCreate, JobListOut, JobOut

router = APIRouter()


@router.get("/companies", response_model=list[CompanyBrief])
def list_companies_brief(db: Session = Depends(get_db)):
    rows = db.query(Company).order_by(Company.name.asc()).all()
    return [
        CompanyBrief(id=c.id, name=c.name, location=c.location, logo_path=c.logo_path)
        for c in rows
    ]


def job_to_out(job: JobPosting, db: Session) -> JobOut:
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


@router.get("/{job_id}", response_model=JobOut)
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
    job = JobPosting(
        company_id=company.id,
        job_role=body.job_role.strip(),
        job_type=body.job_type,
        location=body.location.strip(),
        description=body.description.strip(),
        skills_required=body.skills_required.strip(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job_to_out(job, db)


@router.post("/{job_id}/apply")
def apply_job(
    job_id: int,
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
        raise HTTPException(status_code=400, detail="Already applied to this job")

    app = Application(job_id=job_id, applicant_id=applicant.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"ok": True, "application_id": app.id}
