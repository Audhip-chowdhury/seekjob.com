from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_optional_applicant, get_optional_company
from database import get_db
from models import Applicant, AuthorType, Company, Discussion, JobPosting
from schemas import DiscussionCreate, DiscussionOut, DiscussionReplyCreate

router = APIRouter()


def author_name(db: Session, author_id: int, author_type: AuthorType) -> str:
    if author_type == AuthorType.APPLICANT:
        a = db.query(Applicant).filter(Applicant.id == author_id).first()
        return a.name if a else "Unknown"
    c = db.query(Company).filter(Company.id == author_id).first()
    return c.name if c else "Unknown"


def discussion_to_out(d: Discussion, db: Session) -> DiscussionOut:
    return DiscussionOut(
        id=d.id,
        title=d.title,
        body=d.body,
        job_id=d.job_id,
        company_id=d.company_id,
        author_id=d.author_id,
        author_type=d.author_type,
        author_name=author_name(db, d.author_id, d.author_type),
        parent_id=d.parent_id,
        created_at=d.created_at,
        replies=[],
    )


def build_tree(root: Discussion, db: Session) -> DiscussionOut:
    node = discussion_to_out(root, db)
    children = (
        db.query(Discussion)
        .filter(Discussion.parent_id == root.id)
        .order_by(Discussion.created_at.asc())
        .all()
    )
    node.replies = [build_tree(ch, db) for ch in children]
    return node


@router.get("", response_model=List[DiscussionOut])
def list_threads(
    job_id: Optional[int] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Discussion).filter(Discussion.parent_id.is_(None))
    if job_id is not None:
        q = q.filter(Discussion.job_id == job_id)
    if company_id is not None:
        q = q.filter(Discussion.company_id == company_id)
    roots = q.order_by(Discussion.created_at.desc()).all()
    return [build_tree(r, db) for r in roots]


def find_thread_root(db: Session, discussion_id: int) -> Optional[Discussion]:
    node = db.query(Discussion).filter(Discussion.id == discussion_id).first()
    if not node:
        return None
    while node.parent_id is not None:
        parent = db.query(Discussion).filter(Discussion.id == node.parent_id).first()
        if not parent:
            break
        node = parent
    return node


@router.get("/{thread_id}", response_model=DiscussionOut)
def get_thread(thread_id: int, db: Session = Depends(get_db)):
    root = find_thread_root(db, thread_id)
    if not root:
        raise HTTPException(status_code=404, detail="Thread not found")
    return build_tree(root, db)


def _resolve_author(
    applicant: Optional[Applicant],
    company: Optional[Company],
) -> tuple[int, AuthorType]:
    if applicant and not company:
        return applicant.id, AuthorType.APPLICANT
    if company and not applicant:
        return company.id, AuthorType.COMPANY
    if applicant and company:
        raise HTTPException(status_code=400, detail="Send only one auth token")
    raise HTTPException(status_code=401, detail="Login required to post")


@router.post("", response_model=DiscussionOut)
def create_thread(
    body: DiscussionCreate,
    db: Session = Depends(get_db),
    applicant: Optional[Applicant] = Depends(get_optional_applicant),
    company: Optional[Company] = Depends(get_optional_company),
):
    author_id, author_type = _resolve_author(applicant, company)
    if body.job_id is not None:
        if not db.query(JobPosting).filter(JobPosting.id == body.job_id).first():
            raise HTTPException(status_code=400, detail="Invalid job_id")
    if body.company_id is not None:
        if not db.query(Company).filter(Company.id == body.company_id).first():
            raise HTTPException(status_code=400, detail="Invalid company_id")

    d = Discussion(
        title=body.title.strip() if body.title else "Discussion",
        body=body.body.strip(),
        job_id=body.job_id,
        company_id=body.company_id,
        author_id=author_id,
        author_type=author_type,
        parent_id=None,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return build_tree(d, db)


@router.post("/{thread_id}/reply", response_model=DiscussionOut)
def reply_to_thread(
    thread_id: int,
    body: DiscussionReplyCreate,
    db: Session = Depends(get_db),
    applicant: Optional[Applicant] = Depends(get_optional_applicant),
    company: Optional[Company] = Depends(get_optional_company),
):
    parent_post = db.query(Discussion).filter(Discussion.id == thread_id).first()
    if not parent_post:
        raise HTTPException(status_code=404, detail="Thread not found")
    author_id, author_type = _resolve_author(applicant, company)

    d = Discussion(
        title=None,
        body=body.body.strip(),
        job_id=parent_post.job_id,
        company_id=parent_post.company_id,
        author_id=author_id,
        author_type=author_type,
        parent_id=thread_id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)

    top = find_thread_root(db, thread_id)
    if top:
        return build_tree(top, db)
    return discussion_to_out(d, db)
