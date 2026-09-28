from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class StateOut(ORM):
    id: int; name: str; code: str; type: str; slug: str; description: str | None = None; image_url: str | None = None

class DistrictOut(ORM):
    id: int; state_id: int; name: str; slug: str; description: str | None = None

class CityOut(ORM):
    id: int; district_id: int; name: str; slug: str

class CategoryOut(ORM):
    id: int; name: str; slug: str; icon: str | None = None

class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category_id: int; state_id: int; district_id: int
    city_id: int | None = None; venue_id: int | None = None
    start_date: date; end_date: date
    start_time: str | None = None; price: str | None = None; is_free: bool = False
    organizer: str | None = None; website: str | None = None
    latitude: float | None = None; longitude: float | None = None; featured: bool = False

class EventIn(EventBase):
    slug: str | None = None

class EventOut(EventBase, ORM):
    id: int; slug: str; status: str

class Page(BaseModel):
    total: int; page: int; size: int; items: list[EventOut]

class RegisterIn(BaseModel):
    email: EmailStr; password: str = Field(min_length=8); name: str | None = None

class LoginIn(BaseModel):
    email: EmailStr; password: str

class Token(BaseModel):
    access_token: str; token_type: str = "bearer"

class UserOut(ORM):
    id: int; email: str; name: str | None = None; roles: list[str] = []

class SubmissionIn(BaseModel):
    title: str = Field(min_length=3, max_length=200); description: str = Field(min_length=20, max_length=3000)
    category_slug: str; state_slug: str; district_slug: str | None = None
    venue: str = Field(min_length=2, max_length=200); start_date: date; end_date: date | None = None
    contact_email: EmailStr

class SubmissionOut(SubmissionIn, ORM):
    id: int; status: str
