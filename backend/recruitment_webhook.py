"""
POST to external HworkR public-apply when an applicant applies on SeekJob.

Public-apply JSON may include ``application.candidate_user_id`` (stored as
``recruitment_external_applicant_id``). Older shapes with top-level ``applicant_id`` are still accepted.

Path segment uses ``JobPosting.job_code_requisition_id`` when set (same 6-character ``req_code`` as HworkR).

Inbound pipeline webhooks from HworkR to SeekJob: ``POST /recruitment/application-status`` (see ``routers.applications``).

Env:
  RECRUITMENT_PUBLIC_APPLY_BASE_URL — default http://127.0.0.1:8080
  SEEKJOB_PUBLIC_BASE_URL — base used to build absolute resume_url; default http://127.0.0.1:8020
  HR_BOT_AUTO_HIRE_URL — POST target (default empty = disabled), e.g.
    http://127.0.0.1:8010/hr/screen-seekjob-posting-no-reject
  HR_BOT_AUTO_HIRE_HTTP_TIMEOUT — seconds (default 120)
  HR_BOT_AUTO_HIRE_COMPANY_EMAIL / HR_BOT_AUTO_HIRE_COMPANY_PASSWORD — optional body overrides
    for hr-bot SeekJob login (else hr-bot uses SEEKJOB_COMPANY_EMAIL / SEEKJOB_COMPANY_PASSWORD)
  HR_BOT_AUTO_HIRE_BEARER_TOKEN — optional Authorization Bearer for hr-bot
  HUMAN_PRESENT — ``0`` (default) run auto-hire on apply; ``1`` skip (human handles hiring)
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any
from urllib.parse import quote

import requests

from models import Applicant, JobPosting

logger = logging.getLogger(__name__)

DEFAULT_RECRUITMENT_BASE = "http://127.0.0.1:8080"
DEFAULT_SEEKJOB_PUBLIC = "http://127.0.0.1:8020"
DEFAULT_HR_BOT_AUTO_HIRE_URL = ""
DEFAULT_HR_BOT_AUTO_HIRE_TIMEOUT = 120.0
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


def _human_present_blocks_auto_hire() -> bool:
    """
    When ``HUMAN_PRESENT=1``, skip automatic hr-bot hire triggers (human-in-the-loop mode).
    ``0`` or unset → auto-hire may run when ``HR_BOT_AUTO_HIRE_URL`` is set.
    """
    raw = (os.getenv("HUMAN_PRESENT") or "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _hr_bot_auto_hire_url() -> str:
    return (os.getenv("HR_BOT_AUTO_HIRE_URL") or DEFAULT_HR_BOT_AUTO_HIRE_URL).strip()


def _hr_bot_auto_hire_timeout() -> float:
    raw = (os.getenv("HR_BOT_AUTO_HIRE_HTTP_TIMEOUT") or "").strip()
    if not raw:
        return DEFAULT_HR_BOT_AUTO_HIRE_TIMEOUT
    try:
        return max(1.0, float(raw))
    except ValueError:
        logger.warning("Invalid HR_BOT_AUTO_HIRE_HTTP_TIMEOUT=%r; using default", raw)
        return DEFAULT_HR_BOT_AUTO_HIRE_TIMEOUT


def build_hr_bot_auto_hire_payload(seekjob_job_id: int) -> dict[str, Any]:
    """JSON body for ``POST /hr/screen-seekjob-posting-no-reject``."""
    payload: dict[str, Any] = {
        "seekjob_job_id": int(seekjob_job_id),
        "force_seekjob_screen": False,
        "classify_level_after_seekjob_screen": False,
        "role": {
            "force": False,
            "classify_level_after_screen": False,
            "select_for_role_after_screen": True,
            "select_for_role_force": False,
            "classify_level_after_selection": True,
            "classify_level_force": False,
            "skip_role_per_user_screening": True,
        },
    }
    email = (os.getenv("HR_BOT_AUTO_HIRE_COMPANY_EMAIL") or "").strip()
    password = (os.getenv("HR_BOT_AUTO_HIRE_COMPANY_PASSWORD") or "").strip()
    if email:
        payload["company_email"] = email
    if password:
        payload["company_password"] = password
    return payload


def trigger_hr_bot_auto_hire_seekjob(
    seekjob_job_id: int,
    *,
    application_id: int | None = None,
) -> None:
    """
    Best-effort synchronous POST to hr-bot no-reject screening/hiring pipeline.

    Failures are logged only; callers should not treat exceptions as apply failures.
    """
    if _human_present_blocks_auto_hire():
        logger.debug(
            "hr-bot auto-hire skipped (HUMAN_PRESENT=1) job_id=%s application_id=%s",
            seekjob_job_id,
            application_id,
        )
        return

    url = _hr_bot_auto_hire_url()
    if not url:
        logger.debug(
            "hr-bot auto-hire skipped (HR_BOT_AUTO_HIRE_URL unset) job_id=%s application_id=%s",
            seekjob_job_id,
            application_id,
        )
        return

    payload = build_hr_bot_auto_hire_payload(seekjob_job_id)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (os.getenv("HR_BOT_AUTO_HIRE_BEARER_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    logger.info(
        "hr-bot auto-hire trigger start job_id=%s application_id=%s url=%s",
        seekjob_job_id,
        application_id,
        url,
    )
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=_hr_bot_auto_hire_timeout(),
        )
        text = response.text or ""
        preview = text[:_RESPONSE_BODY_LOG_MAX] + ("…" if len(text) > _RESPONSE_BODY_LOG_MAX else "")
        if response.status_code >= 400:
            logger.warning(
                "hr-bot auto-hire failed status=%s job_id=%s application_id=%s body=%r",
                response.status_code,
                seekjob_job_id,
                application_id,
                preview,
            )
            return
        logger.info(
            "hr-bot auto-hire OK status=%s job_id=%s application_id=%s body=%r",
            response.status_code,
            seekjob_job_id,
            application_id,
            preview,
        )
    except requests.RequestException as exc:
        err_body = ""
        resp = getattr(exc, "response", None)
        if resp is not None:
            t = resp.text or ""
            err_body = t[:_RESPONSE_BODY_LOG_MAX] + ("…" if len(t) > _RESPONSE_BODY_LOG_MAX else "")
        logger.warning(
            "hr-bot auto-hire request error job_id=%s application_id=%s url=%s: %s | response_body=%r",
            seekjob_job_id,
            application_id,
            url,
            exc,
            err_body,
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )


def schedule_hr_bot_auto_hire_on_apply(
    seekjob_job_id: int,
    *,
    application_id: int | None = None,
) -> None:
    """Fire ``trigger_hr_bot_auto_hire_seekjob`` in a daemon thread (non-blocking for apply)."""
    if _human_present_blocks_auto_hire():
        logger.debug(
            "hr-bot auto-hire schedule skipped (HUMAN_PRESENT=1) job_id=%s application_id=%s",
            seekjob_job_id,
            application_id,
        )
        return

    def _run() -> None:
        try:
            trigger_hr_bot_auto_hire_seekjob(
                seekjob_job_id,
                application_id=application_id,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "hr-bot auto-hire background task crashed job_id=%s application_id=%s",
                seekjob_job_id,
                application_id,
            )

    thread = threading.Thread(
        target=_run,
        name=f"hr-bot-auto-hire-{seekjob_job_id}-{application_id or 'na'}",
        daemon=True,
    )
    thread.start()
