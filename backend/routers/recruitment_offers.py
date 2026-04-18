"""
Inbound offer letter webhook from HworkR (``RECRUITMENT_OFFER_WEBHOOK_URL``)
and applicant-facing offer list API.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from auth import get_current_applicant
from database import get_db
from models import Applicant, Application, Company, JobPosting, RecruitmentInboundOffer
from recruitment_matching import normalize_job_posting_code, resolve_application_for_offer
from schemas import (
    OfferRespondIn,
    RecruitmentInboundOfferOut,
    RecruitmentOfferInbound,
    RecruitmentOfferInboundSimple,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure full URL on HworkR: e.g. http://127.0.0.1:8020/recruitment/offers/inbound
RECRUITMENT_OFFER_WEBHOOK_PATH = "/recruitment/offers/inbound"


def _offer_for_applicant(
    db: Session,
    applicant: Applicant,
    offer_pk: int,
) -> RecruitmentInboundOffer | None:
    my_external_ids = [
        r[0]
        for r in db.query(Application.recruitment_external_applicant_id)
        .filter(
            Application.applicant_id == applicant.id,
            Application.recruitment_external_applicant_id.isnot(None),
        )
        .distinct()
        .all()
        if r[0]
    ]
    conds = [RecruitmentInboundOffer.applicant_id == applicant.id]
    if my_external_ids:
        conds.append(
            RecruitmentInboundOffer.recruitment_external_applicant_id.in_(my_external_ids)
        )
    return (
        db.query(RecruitmentInboundOffer)
        .filter(and_(RecruitmentInboundOffer.id == offer_pk, or_(*conds)))
        .first()
    )


def _parse_sent_at(raw: str | None) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        logger.warning("Could not parse offer sent_at=%r", raw)
        return None


def _extract_start_date_from_compensation(comp: Any) -> str | None:
    if not isinstance(comp, dict):
        return None
    ol = comp.get("offer_letter")
    if isinstance(ol, dict):
        joining = ol.get("joining")
        if isinstance(joining, dict):
            d = joining.get("date_of_joining")
            if d is not None and str(d).strip():
                return str(d).strip()
    return None


def _compensation_to_json_str(comp_obj: Any) -> str:
    if comp_obj is None:
        return "{}"
    if isinstance(comp_obj, (dict, list)):
        return json.dumps(comp_obj)
    return json.dumps({"value": comp_obj})


def _resolve_job_posting_by_requisition(db: Session, norm_job: Optional[str]) -> Optional[JobPosting]:
    if not norm_job:
        return None
    for j in db.query(JobPosting).filter(JobPosting.job_code_requisition_id.isnot(None)).all():
        if normalize_job_posting_code(j.job_code_requisition_id) == norm_job:
            return j
    return None


def _resolve_company_external_id(
    db: Session, app_row: Optional[Application], norm_job: Optional[str]
) -> str:
    if app_row:
        job = db.query(JobPosting).filter(JobPosting.id == app_row.job_id).first()
        if job:
            return str(job.company_id)
    jp = _resolve_job_posting_by_requisition(db, norm_job)
    if jp:
        return str(jp.company_id)
    return "0"


def _enrich_offer(row: RecruitmentInboundOffer, db: Session) -> RecruitmentInboundOfferOut:
    job_role = None
    company_name = None
    if row.job_id:
        job = db.query(JobPosting).filter(JobPosting.id == row.job_id).first()
        if job:
            job_role = job.job_role
            c = db.query(Company).filter(Company.id == job.company_id).first()
            company_name = c.name if c else None
    try:
        comp = json.loads(row.compensation_json or "{}")
    except json.JSONDecodeError:
        comp = {}
    if not isinstance(comp, (dict, list)):
        comp = {"value": comp}
    code = row.job_posting_code
    ext_oid = row.external_offer_id
    ext_cid = row.external_company_id
    return RecruitmentInboundOfferOut(
        id=row.id,
        external_offer_id=ext_oid,
        application_id=row.application_id,
        job_id=row.job_id,
        external_company_id=ext_cid,
        recruitment_external_applicant_id=row.recruitment_external_applicant_id,
        job_posting_code=code,
        start_date=row.start_date,
        external_offer_status=row.external_offer_status,
        sent_at=row.sent_at,
        compensation_json=comp,
        job_role=job_role,
        company_name=company_name,
        created_at=row.created_at,
        recruitment_job_id=code,
        external_userid=row.recruitment_external_applicant_id,
        offer_id=ext_oid,
        company_id=ext_cid,
        applicant_response_status=row.applicant_response_status,
        applicant_responded_at=row.applicant_responded_at,
    )


def _persist_legacy_offer(body: RecruitmentOfferInbound, db: Session) -> JSONResponse:
    if body.event != "offer.created":
        logger.warning("Offer webhook: unexpected event=%r (storing anyway)", body.event)

    ext_applicant = body.recruitment_external_applicant_id
    app_row = resolve_application_for_offer(db, ext_applicant, body.job_posting_code)

    comp_obj = body.offer.compensation_json
    comp_str = _compensation_to_json_str(comp_obj)

    sent_at = _parse_sent_at(body.offer.sent_at)
    code_display = None
    if body.job_posting_code and str(body.job_posting_code).strip():
        code_display = str(body.job_posting_code).strip()

    oid = str(body.offer.id).strip()
    now = datetime.utcnow()

    applicant_id = app_row.applicant_id if app_row else None
    application_id = app_row.id if app_row else None
    job_id = app_row.job_id if app_row else None

    existing = (
        db.query(RecruitmentInboundOffer)
        .filter(RecruitmentInboundOffer.external_offer_id == oid)
        .first()
    )

    if existing:
        existing.application_id = application_id
        existing.applicant_id = applicant_id
        existing.job_id = job_id
        existing.external_company_id = str(body.company_id).strip()
        existing.external_application_id = str(body.offer.application_id).strip()
        existing.recruitment_external_applicant_id = ext_applicant
        existing.job_posting_code = code_display
        existing.start_date = body.offer.start_date
        existing.external_offer_status = (
            str(body.offer.status).strip() if body.offer.status is not None else "sent"
        )
        existing.sent_at = sent_at
        existing.compensation_json = comp_str
        existing.event_type = body.event
        existing.updated_at = now
        db.add(existing)
    else:
        db.add(
            RecruitmentInboundOffer(
                external_offer_id=oid,
                application_id=application_id,
                applicant_id=applicant_id,
                job_id=job_id,
                external_company_id=str(body.company_id).strip(),
                external_application_id=str(body.offer.application_id).strip(),
                recruitment_external_applicant_id=ext_applicant,
                job_posting_code=code_display,
                start_date=body.offer.start_date,
                external_offer_status=(
                    str(body.offer.status).strip() if body.offer.status is not None else "sent"
                ),
                sent_at=sent_at,
                compensation_json=comp_str,
                event_type=body.event,
                created_at=now,
                updated_at=now,
            )
        )

    db.commit()
    logger.info(
        "Offer webhook OK external_offer_id=%s seekjob_application_id=%s applicant_id=%s",
        oid,
        application_id,
        applicant_id,
    )
    return JSONResponse(status_code=200, content={"ok": True})


def _persist_simple_offer(body: RecruitmentOfferInboundSimple, db: Session) -> JSONResponse:
    ext_applicant = body.userid
    norm_job = normalize_job_posting_code(str(body.job_id))
    app_row = resolve_application_for_offer(db, ext_applicant, str(body.job_id))

    comp_obj = body.compensation_json
    comp_str = _compensation_to_json_str(comp_obj)
    start_date = _extract_start_date_from_compensation(comp_obj)

    code_display = norm_job if norm_job else str(body.job_id).strip()
    fallback_oid = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"seekjob:offer:{ext_applicant}:{code_display}",
        )
    )
    if body.offer_id is not None:
        s = str(body.offer_id).strip()
        oid = s if s else fallback_oid
    else:
        oid = fallback_oid
    now = datetime.utcnow()

    applicant_id = app_row.applicant_id if app_row else None
    application_id = app_row.id if app_row else None
    job_id: Optional[int] = app_row.job_id if app_row else None
    if job_id is None:
        jp = _resolve_job_posting_by_requisition(db, norm_job)
        if jp:
            job_id = jp.id

    resolved_company = _resolve_company_external_id(db, app_row, norm_job)
    if body.company_id is not None:
        cs = str(body.company_id).strip()
        external_company_id = cs if cs else resolved_company
    else:
        external_company_id = resolved_company

    existing = (
        db.query(RecruitmentInboundOffer)
        .filter(RecruitmentInboundOffer.external_offer_id == oid)
        .first()
    )

    if existing:
        existing.application_id = application_id
        existing.applicant_id = applicant_id
        existing.job_id = job_id
        existing.external_company_id = external_company_id
        existing.recruitment_external_applicant_id = ext_applicant
        existing.job_posting_code = code_display
        existing.start_date = start_date
        existing.external_offer_status = "sent"
        existing.sent_at = None
        existing.compensation_json = comp_str
        existing.event_type = "offer.inbound_simple"
        existing.updated_at = now
        db.add(existing)
    else:
        db.add(
            RecruitmentInboundOffer(
                external_offer_id=oid,
                application_id=application_id,
                applicant_id=applicant_id,
                job_id=job_id,
                external_company_id=external_company_id,
                external_application_id=None,
                recruitment_external_applicant_id=ext_applicant,
                job_posting_code=code_display,
                start_date=start_date,
                external_offer_status="sent",
                sent_at=None,
                compensation_json=comp_str,
                event_type="offer.inbound_simple",
                created_at=now,
                updated_at=now,
            )
        )

    db.commit()
    logger.info(
        "Offer webhook (simple) OK external_offer_id=%s seekjob_application_id=%s applicant_id=%s",
        oid,
        application_id,
        applicant_id,
    )
    return JSONResponse(status_code=200, content={"ok": True})


@router.post(
    RECRUITMENT_OFFER_WEBHOOK_PATH,
    summary="Inbound offer webhook (HworkR → SeekJob)",
    description=(
        "Configure RECRUITMENT_OFFER_WEBHOOK_URL on HworkR to this full URL. "
        "Accepts legacy nested `offer` payloads or compact "
        "`{ job_id, userid, compensation_json, offer_id?, company_id? }`. "
        "No auth in v1 — protect with network controls. Returns 200 with JSON body `{ok: true}`."
    ),
    response_model=None,
)
async def recruitment_offer_inbound_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        raw = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON body") from None
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="JSON object expected")

    if isinstance(raw.get("offer"), dict):
        try:
            body = RecruitmentOfferInbound.model_validate(raw)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors()) from None
        return _persist_legacy_offer(body, db)

    try:
        body = RecruitmentOfferInboundSimple.model_validate(raw)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from None
    return _persist_simple_offer(body, db)


@router.get("/applicant/offers", response_model=list[RecruitmentInboundOfferOut])
def list_my_offers(
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    """Signed-in applicant: offer letters received from HworkR for their profile."""
    my_external_ids = [
        r[0]
        for r in db.query(Application.recruitment_external_applicant_id)
        .filter(
            Application.applicant_id == applicant.id,
            Application.recruitment_external_applicant_id.isnot(None),
        )
        .distinct()
        .all()
        if r[0]
    ]

    conds = [RecruitmentInboundOffer.applicant_id == applicant.id]
    if my_external_ids:
        conds.append(
            RecruitmentInboundOffer.recruitment_external_applicant_id.in_(my_external_ids)
        )

    rows = (
        db.query(RecruitmentInboundOffer)
        .filter(or_(*conds))
        .order_by(RecruitmentInboundOffer.created_at.desc())
        .all()
    )
    return [_enrich_offer(r, db) for r in rows]


@router.get("/applicant/offers/{offer_pk}", response_model=RecruitmentInboundOfferOut)
def get_my_offer(
    offer_pk: int,
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    row = _offer_for_applicant(db, applicant, offer_pk)
    if not row:
        raise HTTPException(status_code=404, detail="Offer not found")
    return _enrich_offer(row, db)


@router.patch("/applicant/offers/{offer_pk}/respond")
def respond_to_offer(
    offer_pk: int,
    body: OfferRespondIn,
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    """
    Forward accept/decline to the recruitment service
    (PATCH .../companies/{company_id}/recruitment/offers/{offer_id}/respond).
    """
    row = _offer_for_applicant(db, applicant, offer_pk)
    if not row:
        raise HTTPException(status_code=404, detail="Offer not found")
    if row.applicant_response_status in ("accepted", "declined"):
        raise HTTPException(status_code=400, detail="You have already responded to this offer")

    company_id = row.external_company_id
    offer_id = row.external_offer_id
    if not company_id or not offer_id:
        raise HTTPException(
            status_code=400,
            detail="Offer is missing company or offer id required for response",
        )

    base = os.getenv("RECRUITMENT_API_BASE", "http://127.0.0.1:8080").rstrip("/")
    path = (
        f"{base}/api/v1/companies/{quote(str(company_id), safe='')}/"
        f"recruitment/offers/{quote(str(offer_id), safe='')}/respond"
    )

    patch_body = {"status": body.status}
    print(f"PATCH {path} body={patch_body}", flush=True)

    try:
        r = requests.patch(path, json=patch_body, timeout=30)
    except requests.RequestException as e:
        logger.exception("Recruitment respond PATCH failed: %s", path)
        raise HTTPException(
            status_code=502,
            detail=f"Recruitment service unreachable: {e!s}",
        ) from e

    if r.status_code >= 400:
        detail = (r.text or "")[:500]
        raise HTTPException(
            status_code=502,
            detail=f"Recruitment service returned {r.status_code}: {detail}",
        )

    row.applicant_response_status = body.status
    row.applicant_responded_at = datetime.utcnow()
    db.add(row)
    db.commit()

    logger.info(
        "Offer respond OK offer_pk=%s status=%s applicant_id=%s",
        offer_pk,
        body.status,
        applicant.id,
    )
    return {"ok": True, "status": body.status}
