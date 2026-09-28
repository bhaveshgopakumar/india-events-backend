from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from .events import published

router = APIRouter(prefix="/api", tags=["locations"])

def one(db, model, slug):
    obj = db.query(model).filter_by(slug=slug).first()
    if not obj: raise HTTPException(404, f"{model.__name__} not found")
    return obj

@router.get("/states", response_model=list[schemas.StateOut])
def states(type: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.State)
    if type: q = q.filter_by(type=type)
    return q.order_by(models.State.name).all()

@router.get("/states/{slug}", response_model=schemas.StateOut)
def state(slug: str, db: Session = Depends(get_db)): return one(db, models.State, slug)

@router.get("/states/{slug}/events", response_model=list[schemas.EventOut])
def state_events(slug: str, db: Session = Depends(get_db)):
    return published(db).filter(models.Event.state_id == one(db, models.State, slug).id).order_by(models.Event.start_date).all()

@router.get("/districts", response_model=list[schemas.DistrictOut])
def districts(state: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.District)
    if state: q = q.join(models.State, models.State.id == models.District.state_id).filter(models.State.slug == state)
    return q.order_by(models.District.name).all()

@router.get("/districts/{slug}", response_model=schemas.DistrictOut)
def district(slug: str, db: Session = Depends(get_db)): return one(db, models.District, slug)

@router.get("/districts/{slug}/events", response_model=list[schemas.EventOut])
def district_events(slug: str, db: Session = Depends(get_db)):
    return published(db).filter(models.Event.district_id == one(db, models.District, slug).id).order_by(models.Event.start_date).all()

@router.get("/cities", response_model=list[schemas.CityOut])
def cities(district: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.City)
    if district: q = q.join(models.District, models.District.id == models.City.district_id).filter(models.District.slug == district)
    return q.order_by(models.City.name).all()

@router.get("/cities/{slug}", response_model=schemas.CityOut)
def city(slug: str, db: Session = Depends(get_db)): return one(db, models.City, slug)

@router.get("/cities/{slug}/events", response_model=list[schemas.EventOut])
def city_events(slug: str, db: Session = Depends(get_db)):
    return published(db).filter(models.Event.city_id == one(db, models.City, slug).id).order_by(models.Event.start_date).all()

@router.get("/categories", response_model=list[schemas.CategoryOut])
def categories(db: Session = Depends(get_db)): return db.query(models.Category).order_by(models.Category.name).all()
