"""
Cards routes:
  GET /cards/       — returns all cards (for frontend display)
  GET /cards/{id}   — returns a single card by id
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db import get_db
from backend.models.card import Card

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/")
async def get_all_cards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Card).order_by(Card.id))
    cards = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "arcane": c.arcane,
            "number": c.number,
            "keywords": c.keywords,
            "upright": c.upright,
            "reversed": c.reversed,
            "image_url": c.image_url,
        }
        for c in cards
    ]


@router.get("/{card_id}")
async def get_card(card_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "id": card.id,
        "name": card.name,
        "arcane": card.arcane,
        "number": card.number,
        "keywords": card.keywords,
        "upright": card.upright,
        "reversed": card.reversed,
        "image_url": card.image_url,
    }
