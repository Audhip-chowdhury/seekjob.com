import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import (
    Base,
    engine,
    migrate_sqlite_application_columns,
    migrate_sqlite_application_unique_job_applicant,
    migrate_sqlite_job_posting_columns,
    migrate_sqlite_recruitment_inbound_offer_response_columns,
    migrate_sqlite_recruitment_inbound_offers,
)
from routers import applications, auth_applicant, auth_company, discussions, jobs, recruitment_offers

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)
migrate_sqlite_job_posting_columns()
migrate_sqlite_application_columns()
migrate_sqlite_application_unique_job_applicant()
migrate_sqlite_recruitment_inbound_offers()
migrate_sqlite_recruitment_inbound_offer_response_columns()

app = FastAPI(
    title="SeekJob API",
    version="1.0.0",
    description=(
        "Inbound recruitment pipeline webhook (configure on HworkR as RECRUITMENT_STATUS_WEBHOOK_URL): "
        "**POST /recruitment/application-status** JSON body: `recruitment_external_applicant_id`, `status`, "
        "optional `job_posting_code` (matches job `job_code_requisition_id`). "
        "Legacy alias: **POST /recruitment/application_status**. "
        "Offer webhook (configure **RECRUITMENT_OFFER_WEBHOOK_URL** on HworkR): **POST /recruitment/offers/inbound** "
        "with JSON `{ job_id, userid, compensation_json, offer_id?, company_id? }` or legacy nested `offer` payload."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_company.router, prefix="/company", tags=["company-auth"])
app.include_router(auth_applicant.router, prefix="/applicant", tags=["applicant-auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="", tags=["applications"])
app.include_router(recruitment_offers.router, prefix="", tags=["recruitment-offers"])
app.include_router(discussions.router, prefix="/discussions", tags=["discussions"])


@app.get("/health")
def health():
    return {"status": "ok"}
