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

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    discussions = relationship("Discussion", back_populates="job_ref")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    status = Column(
        Enum(ApplicationStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=ApplicationStatus.APPLIED,
    )
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("JobPosting", back_populates="applications")
    applicant = relationship("Applicant", back_populates="applications")


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
