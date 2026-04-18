"""
POST to external HworkR public-apply when an applicant applies on SeekJob.

Public-apply JSON may include ``application.candidate_user_id`` (stored as
``recruitment_external_applicant_id``). Older shapes with top-level ``applicant_id`` are still accepted.

Path segment uses ``JobPosting.job_code_requisition_id`` when set (same 6-character ``req_code`` as HworkR).

Inbound pipeline webhooks from HworkR to SeekJob: ``POST /recruitment/application-status`` (see ``routers.applications``).

Env:
  RECRUITMENT_PUBLIC_APPLY_BASE_URL — default http://127.0.0.1:8080
  SEEKJOB_PUBLIC_BASE_URL — base used to build absolute resume_url; default http://127.0.0.1:8020
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import quote

import requests

from models import Applicant, JobPosting

logger = logging.getLogger(__name__)

DEFAULT_RECRUITMENT_BASE = "http://127.0.0.1:8080"
DEFAULT_SEEKJOB_PUBLIC = "http://127.0.0.1:8020"
_RESPONSE_BODY_LOG_MAX = 8000


def _path_segment_for_job(job: JobPosting) -> str:
    """Use job code / requisition id for URL path; fallback to numeric job id."""
    rc = getattr(job, "requisition_code", None)
    if rc and str(rc).strip():
        return str(rc).strip()
    if job.job_code_requisition_id and str(job.job_code_requisition_id).strip():
        return str(job.job_code_requisition_id).strip()
    return str(job.id)


def _resume_url(applicant: Applicant) -> str | None:
    if not applicant.cv_path:
        return None
    base = os.getenv("SEEKJOB_PUBLIC_BASE_URL", DEFAULT_SEEKJOB_PUBLIC).rstrip("/")
    path = str(applicant.cv_path).replace("\\", "/").lstrip("/")
    return f"{base}/uploads/{path}"


def _parse_applicant_id_from_response(response: requests.Response) -> str | None:
    """Extract external id for ``recruitment_external_applicant_id`` from JSON.

    Primary shape: ``application.candidate_user_id``. Fallback: top-level ``applicant_id``
    or ``data.applicant_id``.
    """
    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        logger.warning("Recruitment response is not valid JSON; cannot parse external applicant id")
        return None
    if not isinstance(data, dict):
        return None

    val: Any = None
    app_obj = data.get("application")
    if isinstance(app_obj, dict):
        val = app_obj.get("candidate_user_id")
    if val is None:
        val = data.get("applicant_id")
    if val is None and isinstance(data.get("data"), dict):
        val = data["data"].get("applicant_id")

    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def fire_public_apply_webhook(
    job: JobPosting,
    applicant: Applicant,
    plaintext_password: str | None,
) -> str | None:
    """
    POST to recruitment public-apply. Returns external id string if present (e.g. ``application.candidate_user_id``).
    """
    base = os.getenv("RECRUITMENT_PUBLIC_APPLY_BASE_URL", DEFAULT_RECRUITMENT_BASE).rstrip("/")
    segment = quote(_path_segment_for_job(job), safe="")
    url = f"{base}/api/v1/recruitment/public-apply/{segment}"
    payload = {
        "email": applicant.email,
        "password": plaintext_password,
        "name": applicant.name,
        "resume_url": _resume_url(applicant),
    }
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        text = response.text or ""
        preview = text[:_RESPONSE_BODY_LOG_MAX] + ("…" if len(text) > _RESPONSE_BODY_LOG_MAX else "")
        logger.info(
            "Recruitment public-apply OK status=%s url=%s body=%r",
            response.status_code,
            url,
            preview,
        )
        external_id = _parse_applicant_id_from_response(response)
        if external_id:
            logger.info("Recruitment external applicant id parsed: %s", external_id)
        return external_id
    except requests.RequestException as exc:
        err_body = ""
        resp = getattr(exc, "response", None)
        if resp is not None:
            t = resp.text or ""
            err_body = t[:_RESPONSE_BODY_LOG_MAX] + ("…" if len(t) > _RESPONSE_BODY_LOG_MAX else "")
        logger.warning(
            "Recruitment public-apply webhook failed (%s): %s | response_body=%r",
            url,
            exc,
            err_body,
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )
        return None
