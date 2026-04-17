import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import Applicant, Company

SECRET_KEY = os.getenv("SEEKJOB_SECRET", "dev-secret-change-in-production-min-32-chars!!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except ValueError:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(
    sub: str,
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": sub, "uid": user_id, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_company(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Company:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") != "company":
            raise HTTPException(status_code=403, detail="Company access required")
        uid = payload.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        company = db.query(Company).filter(Company.id == uid).first()
        if not company:
            raise HTTPException(status_code=401, detail="Company not found")
        return company
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_current_applicant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Applicant:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") != "applicant":
            raise HTTPException(status_code=403, detail="Applicant access required")
        uid = payload.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        applicant = db.query(Applicant).filter(Applicant.id == uid).first()
        if not applicant:
            raise HTTPException(status_code=401, detail="Applicant not found")
        return applicant
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_optional_applicant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[Applicant]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") != "applicant":
            return None
        uid = payload.get("uid")
        if not uid:
            return None
        return db.query(Applicant).filter(Applicant.id == uid).first()
    except JWTError:
        return None


def get_optional_company(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[Company]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") != "company":
            return None
        uid = payload.get("uid")
        if not uid:
            return None
        return db.query(Company).filter(Company.id == uid).first()
    except JWTError:
        return None
