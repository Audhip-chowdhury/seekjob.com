import json
from datetime import date, datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models import AuthorType, JobType


# --- Company ---
class CompanyCreate(BaseModel):
    name: str
    location: str
    email: EmailStr
    password: str = Field(min_length=6)


class CompanyLogin(BaseModel):
    email: EmailStr
    password: str


class CompanyOut(BaseModel):
    id: int
    name: str
    location: str
    email: str
    logo_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# --- Applicant ---
class ApplicantCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class ApplicantLogin(BaseModel):
    email: EmailStr
    password: str


class ApplicantOut(BaseModel):
    id: int
    name: str
    email: str
    picture_path: Optional[str] = None
    cv_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Jobs ---
class JobCreate(BaseModel):
    job_role: str
    job_type: JobType
    location: str
    description: str = ""
    skills_required: str = ""

    department_team: Optional[str] = None
    job_level_grade: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    number_of_openings: Optional[int] = Field(default=1, ge=1)
    job_code_requisition_id: Optional[str] = None

    job_summary_purpose: Optional[str] = None
    key_responsibilities: Optional[str] = None
    team_context: Optional[str] = None

    min_education: Optional[str] = None
    years_experience_required: Optional[str] = None
    required_skills_tools: Optional[str] = None
    preferred_skills_nice_to_have: Optional[str] = None

    salary_range_band: Optional[str] = None
    stock_esop_details: Optional[str] = None
    benefits_summary: Optional[str] = None

    application_deadline: Optional[date] = None
    expected_joining_date: Optional[date] = None

    posting_company_name: Optional[str] = None
    company_description_mission: Optional[str] = None
    culture_values: Optional[str] = None


class JobOut(BaseModel):
    id: int
    company_id: int
    job_role: str
    job_type: JobType
    location: str
    description: str
    skills_required: str
    created_at: datetime
    is_active: bool
    company_name: Optional[str] = None
    company_location: Optional[str] = None
    company_logo: Optional[str] = None
    application_count: Optional[int] = None

    department_team: Optional[str] = None
    job_level_grade: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    number_of_openings: int = 1
    job_code_requisition_id: Optional[str] = None

    job_summary_purpose: Optional[str] = None
    key_responsibilities: Optional[str] = None
    team_context: Optional[str] = None

    min_education: Optional[str] = None
    years_experience_required: Optional[str] = None
    required_skills_tools: Optional[str] = None
    preferred_skills_nice_to_have: Optional[str] = None

    salary_range_band: Optional[str] = None
    stock_esop_details: Optional[str] = None
    benefits_summary: Optional[str] = None

    application_deadline: Optional[datetime] = None
    expected_joining_date: Optional[datetime] = None

    posting_company_name: Optional[str] = None
    company_description_mission: Optional[str] = None
    culture_values: Optional[str] = None

    class Config:
        from_attributes = True


class JobListOut(BaseModel):
    items: List[JobOut]
    total: int


class RecruitmentApplyBody(BaseModel):
    """Optional body for POST /jobs/{id}/apply. Password is not stored; forwarded to recruitment API only."""

    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length_when_set(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            return None
        if len(s) < 8:
            raise ValueError("Password must be at least 8 characters")
        return s


class CompanyBrief(BaseModel):
    id: int
    name: str
    location: str
    logo_path: Optional[str] = None

    class Config:
        from_attributes = True


# --- Applications ---
class ApplicationOut(BaseModel):
    id: int
    job_id: int
    applicant_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    recruitment_external_applicant_id: Optional[str] = None
    job_role: Optional[str] = None
    company_name: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applicant_picture_path: Optional[str] = None
    applicant_cv_path: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str


class RecruitmentStatusCallback(BaseModel):
    """Inbound webhook from HworkR (or compatible): pipeline status for a candidate application."""

    recruitment_external_applicant_id: str = Field(
        ...,
        min_length=1,
        description="Candidate platform user id (same as public-apply ``application.candidate_user_id``).",
    )
    status: str = Field(
        ...,
        description="Pipeline stage or row status (e.g. applied, interview, offer, hired, rejected).",
    )
    job_posting_code: Optional[str] = Field(
        None,
        description="6-character requisition code for the posting; matches job ``job_code_requisition_id``. Omit or null for legacy clients.",
    )

    @field_validator("recruitment_external_applicant_id")
    @classmethod
    def strip_external_applicant_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("recruitment_external_applicant_id must not be empty")
        return s

    @field_validator("status")
    @classmethod
    def strip_status(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("status must not be empty")
        return s

    @field_validator("job_posting_code", mode="before")
    @classmethod
    def empty_job_code_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v


# --- Recruitment offer webhook (HworkR → SeekJob) ---
class RecruitmentOfferPayloadIn(BaseModel):
    """Nested ``offer`` object from HworkR ``offer.created`` webhook."""

    model_config = ConfigDict(extra="allow")

    id: str
    application_id: str
    company_id: str
    candidate_user_id: str
    start_date: Optional[str] = None
    status: str
    sent_at: Optional[str] = None
    compensation_json: Optional[dict[str, Any]] = None


class RecruitmentOfferInbound(BaseModel):
    """POST body for ``POST /recruitment/offers/inbound`` (configure ``RECRUITMENT_OFFER_WEBHOOK_URL`` on HworkR)."""

    model_config = ConfigDict(extra="ignore")

    event: str
    company_id: str
    recruitment_external_applicant_id: str
    job_posting_code: Optional[str] = None
    offer: RecruitmentOfferPayloadIn

    @field_validator("recruitment_external_applicant_id")
    @classmethod
    def strip_recruitment_external_applicant_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("recruitment_external_applicant_id must not be empty")
        return s

    @field_validator("job_posting_code", mode="before")
    @classmethod
    def empty_job_posting_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v


class RecruitmentOfferInboundSimple(BaseModel):
    """Compact POST body for ``POST /recruitment/offers/inbound`` (``job_id``, ``userid``, ``compensation_json``)."""

    model_config = ConfigDict(extra="ignore")

    job_id: str | int
    userid: str
    compensation_json: Any
    offer_id: Optional[str | int] = None
    company_id: Optional[str | int] = None

    @field_validator("offer_id", "company_id", mode="before")
    @classmethod
    def empty_optional_ids(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("userid")
    @classmethod
    def strip_userid(cls, v: str) -> str:
        s = str(v).strip()
        if not s:
            raise ValueError("userid must not be empty")
        return s

    @field_validator("job_id", mode="before")
    @classmethod
    def job_id_present(cls, v):
        if v is None:
            raise ValueError("job_id is required")
        if isinstance(v, str) and not str(v).strip():
            raise ValueError("job_id must not be empty")
        return v

    @field_validator("compensation_json", mode="before")
    @classmethod
    def parse_compensation_json(cls, v):
        if v is None:
            raise ValueError("compensation_json is required")
        if isinstance(v, str):
            s = v.strip()
            if not s:
                raise ValueError("compensation_json must not be empty")
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return {"raw_text": v}
        return v


class OfferRespondIn(BaseModel):
    """Applicant accept/decline forwarded to the recruitment API."""

    status: Literal["accepted", "declined"]


class RecruitmentInboundOfferOut(BaseModel):
    id: int
    external_offer_id: str
    application_id: Optional[int] = None
    job_id: Optional[int] = None
    external_company_id: str
    recruitment_external_applicant_id: str
    job_posting_code: Optional[str] = None
    start_date: Optional[str] = None
    external_offer_status: str
    sent_at: Optional[datetime] = None
    compensation_json: Any
    job_role: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime
    recruitment_job_id: Optional[str] = None
    external_userid: Optional[str] = None
    offer_id: Optional[str] = None
    company_id: Optional[str] = None
    applicant_response_status: Optional[str] = None
    applicant_responded_at: Optional[datetime] = None


# --- Discussions ---
class DiscussionCreate(BaseModel):
    title: Optional[str] = None
    body: str
    job_id: Optional[int] = None
    company_id: Optional[int] = None


class DiscussionReplyCreate(BaseModel):
    body: str


class DiscussionAuthorOut(BaseModel):
    name: str
    type: AuthorType


class DiscussionOut(BaseModel):
    id: int
    title: Optional[str] = None
    body: str
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    author_id: int
    author_type: AuthorType
    author_name: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime
    replies: List["DiscussionOut"] = []

    class Config:
        from_attributes = True


DiscussionOut.model_rebuild()
