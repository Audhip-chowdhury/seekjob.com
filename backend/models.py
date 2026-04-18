import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class JobType(str, enum.Enum):
    MANAGEMENT = "Management"
    HR = "HR"
    SOFTWARE_DEV = "Software Dev"
    OPS = "Ops"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class AuthorType(str, enum.Enum):
    APPLICANT = "applicant"
    COMPANY = "company"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    logo_path = Column(String(512), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("JobPosting", back_populates="company")
    discussions = relationship("Discussion", back_populates="company_ref", foreign_keys="Discussion.company_id")


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    picture_path = Column(String(512), nullable=True)
    cv_path = Column(String(512), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="applicant")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    job_role = Column(String(255), nullable=False)
    job_type = Column(
        Enum(JobType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    skills_required = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    department_team = Column(String(255), nullable=True)
    job_level_grade = Column(String(128), nullable=True)
    employment_type = Column(String(64), nullable=True)
    work_mode = Column(String(64), nullable=True)
    number_of_openings = Column(Integer, default=1)
    job_code_requisition_id = Column(String(128), nullable=True)

    job_summary_purpose = Column(Text, nullable=True)
    key_responsibilities = Column(Text, nullable=True)
    team_context = Column(Text, nullable=True)

    min_education = Column(String(255), nullable=True)
    years_experience_required = Column(String(128), nullable=True)
    required_skills_tools = Column(Text, nullable=True)
    preferred_skills_nice_to_have = Column(Text, nullable=True)

    salary_range_band = Column(Text, nullable=True)
    stock_esop_details = Column(Text, nullable=True)
    benefits_summary = Column(Text, nullable=True)

    application_deadline = Column(DateTime, nullable=True)
    expected_joining_date = Column(DateTime, nullable=True)

    posting_company_name = Column(String(255), nullable=True)
    company_description_mission = Column(Text, nullable=True)
    culture_values = Column(Text, nullable=True)

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    discussions = relationship("Discussion", back_populates="job_ref")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "applicant_id", name="uq_applications_job_applicant"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    status = Column(String(255), nullable=False, default="Applied")
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    recruitment_external_applicant_id = Column(String(255), nullable=True)

    job = relationship("JobPosting", back_populates="applications")
    applicant = relationship("Applicant", back_populates="applications")
    inbound_offers = relationship("RecruitmentInboundOffer", back_populates="application")


class RecruitmentInboundOffer(Base):
    """Offer letter pushed from HworkR (``RECRUITMENT_OFFER_WEBHOOK_URL`` → SeekJob)."""

    __tablename__ = "recruitment_inbound_offers"

    id = Column(Integer, primary_key=True, index=True)
    external_offer_id = Column(String(128), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)

    external_company_id = Column(String(128), nullable=False)
    external_application_id = Column(String(36), nullable=True)
    recruitment_external_applicant_id = Column(String(64), nullable=False, index=True)
    job_posting_code = Column(String(16), nullable=True)

    start_date = Column(String(32), nullable=True)
    external_offer_status = Column(String(64), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    compensation_json = Column(Text, nullable=False)  # JSON string
    event_type = Column(String(64), nullable=False, default="offer.created")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applicant_response_status = Column(String(32), nullable=True)
    applicant_responded_at = Column(DateTime, nullable=True)

    application = relationship("Application", back_populates="inbound_offers")


class Discussion(Base):
    __tablename__ = "discussions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)  # null for replies
    body = Column(Text, nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    author_id = Column(Integer, nullable=False)
    author_type = Column(
        Enum(AuthorType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    parent_id = Column(Integer, ForeignKey("discussions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job_ref = relationship("JobPosting", back_populates="discussions")
    company_ref = relationship("Company", back_populates="discussions", foreign_keys=[company_id])
    parent = relationship("Discussion", remote_side=[id], backref="replies")
