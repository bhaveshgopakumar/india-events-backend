import math, re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..db import get_db
from ..auth import require_admin
from .. import models, schemas

router = APIRouter(prefix="/api", tags=["events"])

def published(db: Session):
    return db.query(models.Event).filter(models.Event.status == "published")

def slugify(s: str) -> str: return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", s.lower()))

def km(lat, lng, e):
    if e.latitude is None: return 1e9
    r = math.radians
    h = math.sin(r(e.latitude - lat) / 2) ** 2 + math.cos(r(lat)) * math.cos(r(e.latitude)) * math.sin(r(e.longitude - lng) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))

@router.get("/events", response_model=schemas.Page)
def list_events(
    state: str | None = None, district: str | None = None, city: str | None = None, category: str | None = None,
    q: str | None = None, date_from: date | None = None, date_to: date | None = None, free: bool | None = None,
    featured: bool | None = None, lat: float | None = None, lng: float | None = None, radius_km: float | None = None,
    sort: str = Query("date", pattern="^(date|newest|distance)$"),
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
):
    qs = published(db)
    if state: qs = qs.join(models.State, models.State.id == models.Event.state_id).filter(models.State.slug == state)
    if district: qs = qs.join(models.District, models.District.id == models.Event.district_id).filter(models.District.slug == district)
    if city: qs = qs.join(models.City, models.City.id == models.Event.city_id).filter(models.City.slug == city)
    if category: qs = qs.join(models.Category, models.Category.id == models.Event.category_id).filter(models.Category.slug == category)
    if q: qs = qs.filter(or_(models.Event.title.ilike(f"%{q}%"), models.Event.description.ilike(f"%{q}%")))
    if date_from: qs = qs.filter(models.Event.end_date >= date_from)
    if date_to: qs = qs.filter(models.Event.start_date <= date_to)
    if free is not None: qs = qs.filter(models.Event.is_free == free)
    if featured is not None: qs = qs.filter(models.Event.featured == featured)
    items = qs.order_by(models.Event.created_at.desc() if sort == "newest" else models.Event.start_date).all()
    if lat is not None and lng is not None:
        if radius_km: items = [e for e in items if km(lat, lng, e) <= radius_km]
        if sort == "distance": items.sort(key=lambda e: km(lat, lng, e))
    return {"total": len(items), "page": page, "size": size, "items": items[(page - 1) * size: page * size]}

@router.get("/events/{slug}", response_model=schemas.EventOut)
def get_event(slug: str, db: Session = Depends(get_db)):
    e = published(db).filter(models.Event.slug == slug).first()
    if not e: raise HTTPException(404, "Event not found")
    return e

@router.post("/events", response_model=schemas.EventOut, status_code=201)
def create_event(body: schemas.EventIn, db: Session = Depends(get_db), _=Depends(require_admin)):
    e = models.Event(**body.model_dump(exclude={"slug"}), slug=body.slug or slugify(body.title))
    db.add(e); db.commit(); db.refresh(e); return e

@router.put("/events/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, body: schemas.EventIn, db: Session = Depends(get_db), _=Depends(require_admin)):
    e = db.get(models.Event, event_id)
    if not e: raise HTTPException(404, "Event not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None: setattr(e, k, v)
    db.commit(); db.refresh(e); return e

@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    e = db.get(models.Event, event_id)
    if not e: raise HTTPException(404, "Event not found")
    db.delete(e); db.commit()

@router.get("/search")
def search(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    like = f"%{q}%"
    return {
        "events": [schemas.EventOut.model_validate(e) for e in published(db).filter(or_(models.Event.title.ilike(like), models.Event.description.ilike(like))).limit(20)],
        "states": [schemas.StateOut.model_validate(s) for s in db.query(models.State).filter(models.State.name.ilike(like)).limit(10)],
        "districts": [schemas.DistrictOut.model_validate(d) for d in db.query(models.District).filter(models.District.name.ilike(like)).limit(10)],
    }

@router.get("/calendar", response_model=list[schemas.EventOut])
def calendar(year: int, month: int = Query(ge=1, le=12), state: str | None = None, db: Session = Depends(get_db)):
    start = date(year, month, 1); end = date(year + (month == 12), month % 12 + 1, 1)
    qs = published(db).filter(models.Event.start_date < end, models.Event.end_date >= start)
    if state: qs = qs.join(models.State, models.State.id == models.Event.state_id).filter(models.State.slug == state)
    return qs.order_by(models.Event.start_date).all()
