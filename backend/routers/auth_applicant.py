import os
import secrets
import time
import uuid
from typing import Optional
from urllib.parse import urlencode

import requests as _requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_applicant, hash_password, verify_password
from database import get_db
from models import Applicant
from schemas import ApplicantLogin, ApplicantOut, TokenResponse

router = APIRouter()
BASE_UPLOAD = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
PICTURE_DIR = os.path.join(BASE_UPLOAD, "pictures")
CV_DIR = os.path.join(BASE_UPLOAD, "cvs")
os.makedirs(PICTURE_DIR, exist_ok=True)
os.makedirs(CV_DIR, exist_ok=True)

ALLOWED_PIC = {".jpg", ".jpeg"}
MAX_PIC_BYTES = 5 * 1024 * 1024
ALLOWED_CV = {".pdf"}
MAX_CV_BYTES = 2 * 1024 * 1024

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8020")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

# In-memory CSRF state store: {state: expiry_timestamp}
_oauth_states: dict[str, float] = {}


def _new_state() -> str:
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time() + 600
    return state


def _check_state(state: str) -> bool:
    expiry = _oauth_states.pop(state, None)
    return expiry is not None and time.time() < expiry


def _save_picture(pic_bytes: bytes, pic_ext: str) -> str:
    fname = f"{uuid.uuid4().hex}{pic_ext}"
    with open(os.path.join(PICTURE_DIR, fname), "wb") as f:
        f.write(pic_bytes)
    return f"pictures/{fname}"


def _save_cv(cv_bytes: bytes) -> str:
    fname = f"{uuid.uuid4().hex}.pdf"
    with open(os.path.join(CV_DIR, fname), "wb") as f:
        f.write(cv_bytes)
    return f"cvs/{fname}"


@router.post("/register", response_model=TokenResponse)
async def register_applicant(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    city: str = Form(...),
    country: str = Form(...),
    picture: UploadFile = File(...),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    email_norm = email.strip().lower()
    if db.query(Applicant).filter(Applicant.email == email_norm).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    pic_ext = os.path.splitext(picture.filename or "")[1].lower()
    if pic_ext not in ALLOWED_PIC:
        raise HTTPException(status_code=400, detail="Picture must be JPG or JPEG")
    pic_bytes = await picture.read()
    if len(pic_bytes) > MAX_PIC_BYTES:
        raise HTTPException(status_code=400, detail="Picture must be at most 5MB")

    cv_ext = os.path.splitext(cv.filename or "")[1].lower()
    if cv_ext not in ALLOWED_CV:
        raise HTTPException(status_code=400, detail="CV must be PDF")
    cv_bytes = await cv.read()
    if len(cv_bytes) > MAX_CV_BYTES:
        raise HTTPException(status_code=400, detail="CV must be at most 2MB")

    applicant = Applicant(
        name=name.strip(),
        email=email_norm,
        password_hash=hash_password(password),
        city=city.strip(),
        country=country.strip(),
        picture_path=_save_picture(pic_bytes, pic_ext),
        cv_path=_save_cv(cv_bytes),
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    token = create_access_token(sub=applicant.email, user_id=applicant.id, role="applicant")
    return TokenResponse(access_token=token, role="applicant")


@router.post("/login", response_model=TokenResponse)
def login_applicant(creds: ApplicantLogin, db: Session = Depends(get_db)):
    email_norm = creds.email.strip().lower()
    applicant = db.query(Applicant).filter(Applicant.email == email_norm).first()
    if not applicant or not verify_password(creds.password, applicant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(sub=applicant.email, user_id=applicant.id, role="applicant")
    return TokenResponse(access_token=token, role="applicant")


@router.get("/me", response_model=ApplicantOut)
def me_applicant(applicant: Applicant = Depends(get_current_applicant)):
    return applicant


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/auth/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured — set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars")
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/applicant/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": _new_state(),
        "access_type": "online",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/auth/google/callback")
def google_callback(
    db: Session = Depends(get_db),
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error or not code or not state:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=google_denied")
    if not _check_state(state):
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=invalid_state")

    redirect_uri = f"{BACKEND_URL}/applicant/auth/google/callback"
    token_resp = _requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if not token_resp.ok:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=google_token_failed")

    access_token = token_resp.json().get("access_token", "")
    user_info = _requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    ).json()

    email = (user_info.get("email") or "").strip().lower()
    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=google_no_email")

    name = user_info.get("name") or email.split("@")[0]
    oauth_id = str(user_info.get("sub", ""))

    return _oauth_finish(db, email, name, "google", oauth_id)


# ── GitHub OAuth ──────────────────────────────────────────────────────────────

@router.get("/auth/github")
def github_login():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured — set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET env vars")
    params = urlencode({
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/applicant/auth/github/callback",
        "scope": "user:email",
        "state": _new_state(),
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@router.get("/auth/github/callback")
def github_callback(
    db: Session = Depends(get_db),
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error or not code or not state:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=github_denied")
    if not _check_state(state):
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=invalid_state")

    token_resp = _requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "code": code,
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "redirect_uri": f"{BACKEND_URL}/applicant/auth/github/callback",
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if not token_resp.ok:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=github_token_failed")

    gh_token = token_resp.json().get("access_token", "")
    if not gh_token:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=github_token_failed")

    gh_headers = {"Authorization": f"Bearer {gh_token}", "Accept": "application/json"}
    user_info = _requests.get("https://api.github.com/user", headers=gh_headers, timeout=10).json()

    email = (user_info.get("email") or "").strip().lower()
    if not email:
        emails = _requests.get("https://api.github.com/user/emails", headers=gh_headers, timeout=10).json()
        primary = next((e for e in emails if isinstance(e, dict) and e.get("primary") and e.get("verified")), None)
        email = (primary["email"] if primary else "").strip().lower()

    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login/applicant?error=github_no_email")

    name = user_info.get("name") or user_info.get("login") or email.split("@")[0]
    oauth_id = str(user_info.get("id", ""))

    return _oauth_finish(db, email, name, "github", oauth_id)


# ── Shared OAuth finish ───────────────────────────────────────────────────────

def _oauth_finish(db: Session, email: str, name: str, provider: str, oauth_id: str) -> RedirectResponse:
    applicant = db.query(Applicant).filter(Applicant.email == email).first()
    if applicant is None:
        applicant = Applicant(
            name=name,
            email=email,
            password_hash=hash_password(uuid.uuid4().hex),
            oauth_provider=provider,
            oauth_id=oauth_id,
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
        needs_profile = True
    else:
        if not applicant.oauth_provider:
            applicant.oauth_provider = provider
            applicant.oauth_id = oauth_id
            db.commit()
        needs_profile = not bool(applicant.city and applicant.country and applicant.cv_path)

    token = create_access_token(sub=applicant.email, user_id=applicant.id, role="applicant")
    params = urlencode({"token": token, "role": "applicant", "needs_profile": str(needs_profile).lower()})
    return RedirectResponse(f"{FRONTEND_URL}/oauth-callback?{params}")


# ── Complete profile (for OAuth users) ───────────────────────────────────────

@router.post("/complete-profile", response_model=ApplicantOut)
async def complete_profile(
    city: str = Form(...),
    country: str = Form(...),
    picture: Optional[UploadFile] = File(None),
    cv: Optional[UploadFile] = File(None),
    applicant: Applicant = Depends(get_current_applicant),
    db: Session = Depends(get_db),
):
    applicant.city = city.strip()
    applicant.country = country.strip()

    if picture and picture.filename:
        pic_ext = os.path.splitext(picture.filename)[1].lower()
        if pic_ext not in ALLOWED_PIC:
            raise HTTPException(status_code=400, detail="Picture must be JPG or JPEG")
        pic_bytes = await picture.read()
        if len(pic_bytes) > MAX_PIC_BYTES:
            raise HTTPException(status_code=400, detail="Picture must be at most 5MB")
        applicant.picture_path = _save_picture(pic_bytes, pic_ext)

    if cv and cv.filename:
        cv_ext = os.path.splitext(cv.filename)[1].lower()
        if cv_ext not in ALLOWED_CV:
            raise HTTPException(status_code=400, detail="CV must be PDF")
        cv_bytes = await cv.read()
        if len(cv_bytes) > MAX_CV_BYTES:
            raise HTTPException(status_code=400, detail="CV must be at most 2MB")
        applicant.cv_path = _save_cv(cv_bytes)

    db.commit()
    db.refresh(applicant)
    return applicant
