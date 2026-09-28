"""Seed India, all 36 states/UTs, sample districts, categories and events.
Usage: python -m app.seed [--admin EMAIL PASSWORD]"""
import json, sys
from datetime import date
from pathlib import Path
from .db import SessionLocal
from . import models
from .auth import hash_pw

data = json.loads((Path(__file__).parent / "seed_data.json").read_text())

def make_admin(db, email, pw):
    u = models.User(email=email.lower(), password_hash=hash_pw(pw)); db.add(u); db.flush()
    db.add(models.UserRole(user_id=u.id, role="admin"))

def run():
    db = SessionLocal()
    if not db.query(models.Country).first():
        india = models.Country(name="India", code="IN", slug="india"); db.add(india); db.flush()
        st, di, ci, cat = {}, {}, {}, {}
        for s in data["states"]:
            st[s["slug"]] = models.State(country_id=india.id, name=s["name"], code=s["code"], type=s["type"], slug=s["slug"])
        db.add_all(st.values()); db.flush()
        for d in data["districts"]:
            di[d["slug"]] = models.District(state_id=st[d["stateSlug"]].id, name=d["name"], slug=d["slug"])
        db.add_all(di.values()); db.flush()
        for c in data["cities"]:
            ci[c["slug"]] = models.City(district_id=di[c["districtSlug"]].id, name=c["name"], slug=c["slug"])
        for c in data["categories"]:
            cat[c["slug"]] = models.Category(name=c["name"], slug=c["slug"], icon=c["emoji"])
        db.add_all([*ci.values(), *cat.values()]); db.flush()
        for e in data["events"]:
            v = models.Venue(city_id=ci[e["citySlug"]].id, name=e["venue"], latitude=e["lat"], longitude=e["lng"]); db.add(v); db.flush()
            db.add(models.Event(title=e["title"], slug=e["slug"], description=e["description"], category_id=cat[e["category"]].id,
                state_id=st[e["stateSlug"]].id, district_id=di[e["districtSlug"]].id, city_id=ci[e["citySlug"]].id, venue_id=v.id,
                start_date=date.fromisoformat(e["startDate"]), end_date=date.fromisoformat(e["endDate"]), start_time=e["time"],
                price=e["price"], is_free=e["price"] == "Free", organizer=e["organizer"], latitude=e["lat"], longitude=e["lng"],
                featured=bool(e.get("featured"))))
        print("Seeded locations and events")
    if len(sys.argv) == 4 and sys.argv[1] == "--admin":
        make_admin(db, sys.argv[2], sys.argv[3]); print("Admin created")
    db.commit()

if __name__ == "__main__":
    run()
