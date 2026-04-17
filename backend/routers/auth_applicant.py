import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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


@router.post("/register", response_model=TokenResponse)
async def register_applicant(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
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
    pic_fname = f"{uuid.uuid4().hex}{pic_ext}"
    pic_path_fs = os.path.join(PICTURE_DIR, pic_fname)
    with open(pic_path_fs, "wb") as f:
        f.write(pic_bytes)
    picture_path = f"pictures/{pic_fname}"

    cv_ext = os.path.splitext(cv.filename or "")[1].lower()
    if cv_ext not in ALLOWED_CV:
        raise HTTPException(status_code=400, detail="CV must be PDF")
    cv_bytes = await cv.read()
    if len(cv_bytes) > MAX_CV_BYTES:
        raise HTTPException(status_code=400, detail="CV must be at most 2MB")
    cv_fname = f"{uuid.uuid4().hex}{cv_ext}"
    cv_path_fs = os.path.join(CV_DIR, cv_fname)
    with open(cv_path_fs, "wb") as f:
        f.write(cv_bytes)
    cv_path = f"cvs/{cv_fname}"

    applicant = Applicant(
        name=name.strip(),
        email=email_norm,
        password_hash=hash_password(password),
        picture_path=picture_path,
        cv_path=cv_path,
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
