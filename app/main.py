from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import locations, events, users

app = FastAPI(title="India Events API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"])
for r in (locations.router, events.router, users.router):
    app.include_router(r)

@app.get("/health")
def health(): return {"ok": True}
