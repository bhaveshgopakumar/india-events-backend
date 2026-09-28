from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..auth import hash_pw, verify_pw, make_token, current_user, roles_of, require_admin
from .. import models, schemas
from .events import slugify

router = APIRouter(prefix="/api", tags=["users"])

@router.post("/auth/register", response_model=schemas.Token, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(email=body.email.lower()).first(): raise HTTPException(409, "Email already registered")
    u = models.User(email=body.email.lower(), name=body.name, password_hash=hash_pw(body.password))
    db.add(u); db.flush(); db.add(models.UserRole(user_id=u.id, role="user")); db.commit()
    return {"access_token": make_token(u.id)}

@router.post("/auth/login", response_model=schemas.Token)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    u = db.query(models.User).filter_by(email=body.email.lower()).first()
    if not u or not verify_pw(body.password, u.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"access_token": make_token(u.id)}

@router.get("/auth/me", response_model=schemas.UserOut)
def me(user=Depends(current_user), db: Session = Depends(get_db)):
    return schemas.UserOut(id=user.id, email=user.email, name=user.name, roles=roles_of(db, user.id))

@router.get("/bookmarks", response_model=list[schemas.EventOut])
def bookmarks(user=Depends(current_user), db: Session = Depends(get_db)):
    return db.query(models.Event).join(models.Bookmark, models.Bookmark.event_id == models.Event.id).filter(models.Bookmark.user_id == user.id).all()

@router.post("/bookmarks/{event_id}", status_code=201)
def add_bookmark(event_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(models.Event, event_id): raise HTTPException(404, "Event not found")
    if not db.query(models.Bookmark).filter_by(user_id=user.id, event_id=event_id).first():
        db.add(models.Bookmark(user_id=user.id, event_id=event_id)); db.commit()
    return {"ok": True}

@router.delete("/bookmarks/{event_id}", status_code=204)
def del_bookmark(event_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    db.query(models.Bookmark).filter_by(user_id=user.id, event_id=event_id).delete(); db.commit()

@router.post("/event-submissions", response_model=schemas.SubmissionOut, status_code=201)
def submit(body: schemas.SubmissionIn, db: Session = Depends(get_db)):
    s = models.EventSubmission(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@router.get("/admin/event-submissions", response_model=list[schemas.SubmissionOut])
def list_subs(status: str | None = None, db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(models.EventSubmission)
    if status: q = q.filter_by(status=status)
    return q.order_by(models.EventSubmission.created_at.desc()).all()

def _sub(db, sid):
    s = db.get(models.EventSubmission, sid)
    if not s: raise HTTPException(404, "Submission not found")
    return s

@router.put("/admin/event-submissions/{sid}/approve", response_model=schemas.EventOut)
def approve(sid: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = _sub(db, sid)
    st = db.query(models.State).filter_by(slug=s.state_slug).first()
    di = db.query(models.District).filter_by(slug=s.district_slug).first() if s.district_slug else None
    cat = db.query(models.Category).filter_by(slug=s.category_slug).first()
    if not (st and di and cat): raise HTTPException(400, "Submission needs a valid state, district and category")
    e = models.Event(title=s.title, slug=f"{slugify(s.title)}-{s.id}", description=s.description, category_id=cat.id, state_id=st.id,
                     district_id=di.id, start_date=s.start_date, end_date=s.end_date or s.start_date, organizer=s.contact_email)
    s.status = "approved"; db.add(e); db.commit(); db.refresh(e); return e

@router.put("/admin/event-submissions/{sid}/reject", response_model=schemas.SubmissionOut)
def reject(sid: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = _sub(db, sid); s.status = "rejected"; db.commit(); db.refresh(s); return s
