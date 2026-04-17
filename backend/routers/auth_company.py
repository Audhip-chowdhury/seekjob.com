import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_company, hash_password, verify_password
from database import get_db
from models import Company
from schemas import CompanyLogin, CompanyOut, TokenResponse

router = APIRouter()
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "logos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_LOGO = {".jpg", ".jpeg", ".png"}
MAX_LOGO_BYTES = 5 * 1024 * 1024


@router.post("/register", response_model=TokenResponse)
async def register_company(
    name: str = Form(...),
    location: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    email_norm = email.strip().lower()
    if db.query(Company).filter(Company.email == email_norm).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    logo_path = None
    if logo and logo.filename:
        ext = os.path.splitext(logo.filename)[1].lower()
        if ext not in ALLOWED_LOGO:
            raise HTTPException(status_code=400, detail="Logo must be JPG or PNG")
        contents = await logo.read()
        if len(contents) > MAX_LOGO_BYTES:
            raise HTTPException(status_code=400, detail="Logo must be at most 5MB")
        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        with open(fpath, "wb") as f:
            f.write(contents)
        logo_path = f"logos/{fname}"

    company = Company(
        name=name.strip(),
        location=location.strip(),
        email=email_norm,
        password_hash=hash_password(password),
        logo_path=logo_path,
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    token = create_access_token(sub=company.email, user_id=company.id, role="company")
    return TokenResponse(access_token=token, role="company")


@router.post("/login", response_model=TokenResponse)
def login_company(creds: CompanyLogin, db: Session = Depends(get_db)):
    email_norm = creds.email.strip().lower()
    company = db.query(Company).filter(Company.email == email_norm).first()
    if not company or not verify_password(creds.password, company.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(sub=company.email, user_id=company.id, role="company")
    return TokenResponse(access_token=token, role="company")


@router.get("/me", response_model=CompanyOut)
def me_company(company: Company = Depends(get_current_company)):
    return company
