"""
Routes Stripe :
  POST /stripe/checkout   — crée une session de paiement
  POST /stripe/portal     — redirige vers le portail de gestion d'abonnement
  POST /stripe/webhook    — reçoit les événements Stripe (paiement, annulation...)
"""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db import get_db
from backend.models.user import User
from backend.services.auth import require_user
from backend.services.stripe import create_checkout_session, create_portal_session
from backend.config import get_settings

router = APIRouter(prefix="/stripe", tags=["stripe"])
settings = get_settings()


@router.post("/checkout")
async def checkout(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """Génère l'URL de paiement Stripe Checkout."""
    if user.is_premium:
        raise HTTPException(status_code=400, detail="Tu es déjà abonné premium")

    url = await create_checkout_session(
        user_id=str(user.id),
        user_email=user.email,
        customer_id=user.stripe_customer_id,
    )
    return {"checkout_url": url}


@router.post("/portal")
async def portal(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """Génère l'URL du portail Stripe pour gérer l'abonnement."""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Aucun abonnement Stripe associé")

    url = await create_portal_session(user.stripe_customer_id)
    return {"portal_url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Reçoit les webhooks Stripe et met à jour le statut premium en base.
    Events gérés :
      - checkout.session.completed      → active le premium
      - customer.subscription.deleted   → désactive le premium
      - invoice.payment_failed          → désactive le premium
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Signature Stripe invalide")

    # ── checkout.session.completed → activer premium ────────
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_premium = True
                user.stripe_customer_id = customer_id
                user.stripe_subscription_id = subscription_id
                await db.commit()

    # ── customer.subscription.deleted → désactiver premium ─
    elif event["type"] in ("customer.subscription.deleted", "invoice.payment_failed"):
        obj = event["data"]["object"]
        customer_id = obj.get("customer")

        if customer_id:
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.is_premium = False
                user.stripe_subscription_id = None
                await db.commit()

    return {"status": "ok"}
