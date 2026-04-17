from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from models import ApplicationStatus, AuthorType, JobType


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
    description: str
    skills_required: str


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

    class Config:
        from_attributes = True


class JobListOut(BaseModel):
    items: List[JobOut]
    total: int


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
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    job_role: Optional[str] = None
    company_name: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applicant_picture_path: Optional[str] = None
    applicant_cv_path: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


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
