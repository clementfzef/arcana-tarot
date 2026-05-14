"""
Routes de tirage :
  POST /tirages/         — effectue un tirage (avec quota check)
  GET  /tirages/         — historique de l'utilisateur connecté
  GET  /tirages/quota    — quota restant aujourd'hui
"""

import uuid
from datetime import date, timezone, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from backend.db import get_db
from backend.models.card import Card
from backend.models.tirage import Tirage
from backend.models.quota import Quota
from backend.models.user import User
from backend.services.auth import get_current_user
from backend.services.shuffle import tirer_cartes, PREMIUM_TIRAGES, NB_CARTES
from backend.services.groq_service import generer_interpretation
from backend.config import get_settings

router = APIRouter(prefix="/tirages", tags=["tirages"])
settings = get_settings()

TirageType = Literal["1_carte", "oui_non", "passe_present_futur", "croix_celtique"]


# ── Helpers quota ───────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


async def check_and_increment_quota(
    db: AsyncSession,
    user: User | None,
    ip: str,
) -> int:
    """Vérifie et incrémente le quota. Retourne le count après incrémentation."""
    today = date.today()

    if user:
        # Utilisateur connecté — quota par user_id
        result = await db.execute(
            select(Quota).where(Quota.user_id == user.id, Quota.date == today)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            quota = Quota(user_id=user.id, date=today, count=0)
            db.add(quota)
    else:
        # Anonyme — quota par IP
        result = await db.execute(
            select(Quota).where(Quota.ip == ip, Quota.date == today, Quota.user_id == None)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            quota = Quota(ip=ip, date=today, count=0)
            db.add(quota)

    if quota.count >= settings.daily_free_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite quotidienne de {settings.daily_free_limit} tirages gratuits atteinte. Revenez demain ou passez au premium.",
        )

    quota.count += 1
    await db.flush()
    return quota.count


# ── Schémas ────────────────────────────────────────────────

class TirageRequest(BaseModel):
    type: TirageType


class CarteResult(BaseModel):
    id: int
    nom: str
    position: str
    inversee: bool
    keywords: list[str]
    interpretation_statique: str  # texte de base toujours présent


class TirageResponse(BaseModel):
    id: str
    type: str
    cartes: list[CarteResult]
    quota_restant: int | None  # None si premium


# ── Routes ─────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def effectuer_tirage(
    body: TirageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    # Vérifier accès premium pour certains tirages
    if body.type in PREMIUM_TIRAGES:
        if not user or not user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Le tirage '{body.type}' est réservé aux abonnés premium.",
            )

    # Vérifier et incrémenter le quota (sauf premium)
    quota_restant = None
    if not (user and user.is_premium):
        ip = get_client_ip(request)
        count = await check_and_increment_quota(db, user, ip)
        quota_restant = max(0, settings.daily_free_limit - count)

    # Récupérer tous les IDs de cartes
    result = await db.execute(select(Card.id))
    all_ids = [row[0] for row in result.fetchall()]

    # Tirer les cartes
    drawn = tirer_cartes(body.type, all_ids)

    # Récupérer les données complètes des cartes tirées
    card_ids = [d["card_id"] for d in drawn]
    cards_result = await db.execute(select(Card).where(Card.id.in_(card_ids)))
    cards_map = {c.id: c for c in cards_result.scalars().all()}

    # Construire le résultat
    cartes_result = []
    cartes_jsonb = []
    for d in drawn:
        card = cards_map[d["card_id"]]
        interp = card.reversed if d["inversee"] else card.upright
        cartes_result.append(
            CarteResult(
                id=card.id,
                nom=card.name,
                position=d["position"],
                inversee=d["inversee"],
                keywords=card.keywords,
                interpretation_statique=interp,
            )
        )
        cartes_jsonb.append({
            "id": card.id,
            "nom": card.name,
            "position": d["position"],
            "inversee": d["inversee"],
            "keywords": card.keywords,
            "interpretation_statique": interp,
        })

    # Sauvegarder le tirage si utilisateur connecté
    tirage_id = str(uuid.uuid4())
    if user:
        tirage = Tirage(
            id=uuid.UUID(tirage_id),
            user_id=user.id,
            type=body.type,
            cartes=cartes_jsonb,
        )
        db.add(tirage)

    return {
        "id": tirage_id,
        "type": body.type,
        "cartes": [c.model_dump() for c in cartes_result],
        "quota_restant": quota_restant,
    }


@router.post("/stream/interpret")
async def streamer_interpretation(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """
    Lance la génération LLM en streaming pour un tirage.
    Retourne un text/event-stream (SSE).
    """
    # Récupérer le tirage (uniquement si sauvegardé, i.e. utilisateur connecté)
    # Pour les anonymes, les cartes sont passées dans le body de la requête
    body = await request.json()
    cartes = body.get("cartes", [])
    type_tirage = body.get("type", "1_carte")
    question = body.get("question", "")
    is_premium = user.is_premium if user else False

    if not cartes:
        raise HTTPException(status_code=400, detail="Données du tirage manquantes")

    return StreamingResponse(
        generer_interpretation(cartes, type_tirage, is_premium, question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/quota")
async def get_quota(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Retourne le quota restant pour aujourd'hui."""
    if user and user.is_premium:
        return {"quota_restant": None, "is_premium": True}

    today = date.today()
    if user:
        result = await db.execute(
            select(Quota).where(Quota.user_id == user.id, Quota.date == today)
        )
    else:
        ip = get_client_ip(request)
        result = await db.execute(
            select(Quota).where(Quota.ip == ip, Quota.date == today, Quota.user_id == None)
        )
    quota = result.scalar_one_or_none()
    count = quota.count if quota else 0
    return {
        "quota_restant": max(0, settings.daily_free_limit - count),
        "quota_total": settings.daily_free_limit,
        "is_premium": False,
    }


@router.get("/historique")
async def historique(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Retourne l'historique des tirages (utilisateur connecté uniquement)."""
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise pour voir l'historique")

    limit = None if user.is_premium else 10
    query = (
        select(Tirage)
        .where(Tirage.user_id == user.id)
        .order_by(Tirage.created_at.desc())
    )
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    tirages = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "type": t.type,
            "cartes": t.cartes,
            "created_at": t.created_at.isoformat(),
        }
        for t in tirages
    ]
