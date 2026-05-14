"""
Service Stripe — création de session de paiement et portail client.
"""

import stripe
from backend.config import get_settings

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


async def create_checkout_session(user_id: str, user_email: str, customer_id: str | None) -> str:
    """Crée une session Stripe Checkout et retourne l'URL de paiement."""
    params = {
        "payment_method_types": ["card"],
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
        "success_url": f"{settings.frontend_url}/premium/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.frontend_url}/premium",
        "metadata": {"user_id": user_id},
        "subscription_data": {"metadata": {"user_id": user_id}},
    }
    # Réutiliser le customer Stripe si déjà existant
    if customer_id:
        params["customer"] = customer_id
    else:
        params["customer_email"] = user_email

    session = stripe.checkout.Session.create(**params)
    return session.url


async def create_portal_session(stripe_customer_id: str) -> str:
    """Crée un portail Stripe pour que l'utilisateur gère son abonnement."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/profil",
    )
    return session.url
