"""
Resolve SeekJob ``Application`` rows from HworkR identifiers (external applicant id + optional job code).
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Application, JobPosting

logger = logging.getLogger(__name__)


def normalize_job_posting_code(value: Optional[str]) -> Optional[str]:
    """Uppercase trimmed requisition code; None / blank → None (legacy webhook)."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.upper()


def application_matches_job_code(db: Session, app: Application, code_norm: str) -> bool:
    job = db.query(JobPosting).filter(JobPosting.id == app.job_id).first()
    if not job:
        return False
    jc = normalize_job_posting_code(job.job_code_requisition_id)
    return jc == code_norm


def resolve_application_strict(
    db: Session,
    external_id: str,
    job_posting_code: Optional[str],
    *,
    log_prefix: str,
) -> Application:
    """Pipeline status webhook: raise HTTPException on missing / ambiguous rows."""
    apps = (
        db.query(Application)
        .filter(Application.recruitment_external_applicant_id == external_id)
        .all()
    )
    if not apps:
        logger.info(
            "%s: 404 — no application for recruitment_external_applicant_id=%r",
            log_prefix,
            external_id,
        )
        raise HTTPException(
            status_code=404,
            detail="No application found for this recruitment_external_applicant_id",
        )

    code_norm = normalize_job_posting_code(job_posting_code)
    if code_norm is not None:
        matched = [a for a in apps if application_matches_job_code(db, a, code_norm)]
        if len(matched) == 1:
            return matched[0]
        if not matched:
            logger.info(
                "%s: 404 — no row matches recruitment_external_applicant_id=%r and job_posting_code=%r",
                log_prefix,
                external_id,
                code_norm,
            )
            raise HTTPException(
                status_code=404,
                detail="No application matches recruitment_external_applicant_id and job_posting_code",
            )
        logger.warning(
            "Multiple rows matched external id %r and job_posting_code %r; using first application_id=%s",
            external_id,
            code_norm,
            matched[0].id,
        )
        return matched[0]

    if len(apps) == 1:
        return apps[0]

    raise HTTPException(
        status_code=409,
        detail=(
            "Multiple applications share this recruitment_external_applicant_id; "
            "include job_posting_code to select the correct posting"
        ),
    )


def resolve_application_for_offer(
    db: Session,
    external_id: str,
    job_posting_code: Optional[str],
) -> Optional[Application]:
    """
    Offer webhook: return a single Application when uniquely resolvable; otherwise None (offer still stored).
    """
    apps = (
        db.query(Application)
        .filter(Application.recruitment_external_applicant_id == external_id)
        .all()
    )
    if not apps:
        logger.warning(
            "Offer webhook: no Application for recruitment_external_applicant_id=%r — storing offer unlinked",
            external_id,
        )
        return None

    code_norm = normalize_job_posting_code(job_posting_code)
    if code_norm is not None:
        matched = [a for a in apps if application_matches_job_code(db, a, code_norm)]
        if len(matched) == 1:
            return matched[0]
        if not matched:
            logger.warning(
                "Offer webhook: no Application matches external id %r and job_posting_code %r — storing unlinked",
                external_id,
                code_norm,
            )
            return None
        logger.warning(
            "Offer webhook: multiple Applications for external id %r and code %r; using first application_id=%s",
            external_id,
            code_norm,
            matched[0].id,
        )
        return matched[0]

    if len(apps) == 1:
        return apps[0]

    logger.warning(
        "Offer webhook: multiple Applications share recruitment_external_applicant_id=%r without job_posting_code — storing unlinked",
        external_id,
    )
    return None
