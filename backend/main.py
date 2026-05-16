"""
Point d'entrée FastAPI — site de tarot interactif.
Lancement : uvicorn backend.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import get_settings
from backend.routers import auth, tirages, stripe_webhooks, cards

settings = get_settings()

# Rate limiter : protège auth contre brute force, et tirages contre abus
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="Tarot API",
    description="API pour le site de tarot interactif",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ────────────────────────────────────────────────────
# FRONTEND_URL can be a comma-separated list for multi-origin support
_origins = [o.strip() for o in settings.frontend_url.split(",") if o.strip()]
_origins += ["http://localhost:3000", "http://localhost:5500", "http://127.0.0.1:5500"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(tirages.router)
app.include_router(stripe_webhooks.router)
app.include_router(cards.router)


@app.get("/")
async def root():
    return {"message": "Tarot API opérationnelle", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
