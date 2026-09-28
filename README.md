# India Events API — FastAPI + MySQL + SQLAlchemy + Alembic

## Run
    docker compose up --build
API at http://localhost:8000, interactive docs at http://localhost:8000/docs

## Create an admin
    docker compose exec api python -m app.seed --admin you@example.com a-strong-password

## Data model
Country → State/UT → District → City → Venue → Event, plus categories, users, user_roles (separate table), bookmarks, event_submissions.
All 36 states/UTs are seeded with sample districts and events. Add more through the admin endpoints — no code changes needed.

## Endpoints
- /api/states, /api/states/{slug}, /api/states/{slug}/events (same for districts, cities)
- /api/events (filters: state, district, city, category, q, date_from, date_to, free, featured, lat, lng, radius_km, sort, page, size)
- /api/events/{slug}; POST/PUT/DELETE /api/events (admin)
- /api/search?q=, /api/calendar?year=&month=, /api/categories
- /api/auth/register, /api/auth/login, /api/auth/me
- /api/bookmarks, POST/DELETE /api/bookmarks/{event_id}
- POST /api/event-submissions; admin: GET /api/admin/event-submissions, PUT .../{id}/approve|reject

## Deploy
Any Docker host (Render, Railway, Fly.io, a VPS). Set SECRET_KEY, DATABASE_URL and CORS_ORIGINS to your website's address.
