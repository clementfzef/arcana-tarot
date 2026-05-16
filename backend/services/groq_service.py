"""
Service Groq — interprétation tarot en streaming (SSE).
Modèle : llama-3.3-70b-versatile
Free tier : 14 400 req/jour, 30 req/min — aucune CB requise.
"""

import json
from typing import AsyncGenerator
from groq import AsyncGroq
from backend.config import get_settings

settings = get_settings()

SPREAD_NAMES = {
    "1_carte":             "Single Card",
    "oui_non":             "Yes / No",
    "passe_present_futur": "Past / Present / Future",
    "croix_celtique":      "Sacred Cross (5-card spread)",
}


def _card_block(c: dict) -> str:
    """Format a single card with explicit orientation + canonical meaning."""
    name        = c["nom"]
    position    = c["position"]
    inversee    = bool(c.get("inversee"))
    orientation = "REVERSED ↻" if inversee else "UPRIGHT ↑"
    base_text   = (c.get("interpretation_statique") or "").strip()
    keywords    = ", ".join(c.get("keywords", []))

    return (
        f"• Position \"{position}\" — {name} [{orientation}]\n"
        f"  Keywords: {keywords}\n"
        f"  Canonical meaning in this orientation: {base_text}"
    )


def build_prompt(cartes: list[dict], type_tirage: str, is_premium: bool, question: str = "") -> str:
    length = "detailed and rich (approximately 250 words per card)" if is_premium \
             else "concise and evocative (approximately 80 words per card)"

    cards_text = "\n\n".join(_card_block(c) for c in cartes)

    # Count how many cards landed upright vs reversed — useful for spread overview
    upright_count = sum(1 for c in cartes if not c.get("inversee"))
    reversed_count = len(cartes) - upright_count
    orientation_summary = f"Spread balance: {upright_count} upright · {reversed_count} reversed."

    question_block = f'\nThe seeker\'s question: "{question}"\n' if question.strip() else ""

    # Orientation rules — explicit instructions on how to use upright vs reversed
    orientation_rules = """
ORIENTATION RULES (CRITICAL — apply faithfully):
- UPRIGHT cards express the card's direct, manifest, outward energy. Lean into the canonical upright meaning given above.
- REVERSED cards express the SHADOW side of that energy: the meaning may be blocked, internalised, delayed, denied, excessive, or expressed unhealthily. Interpret reversed cards through their canonical reversed meaning given above — do NOT simply invert keywords. They often signal something the seeker is resisting, has not yet integrated, or is being asked to release.
- Treat reversed cards with compassion, never as "bad omens" — they are invitations to growth.
- Mixing matters: if most cards are reversed, the reading is introspective / shadow work; if most are upright, the reading is active / outward-facing. Reflect that balance in your opening overview."""

    # Special instructions for Yes/No spreads — must give a clear verdict
    yesno_instructions = ""
    if type_tirage == "oui_non":
        yesno_instructions = (
            "\n- This is a YES / NO reading. You MUST open with a clear, single-word verdict on its own line:\n"
            "  • Upright + favorable energy for the question → **YES**.\n"
            "  • Reversed OR clearly unfavorable energy → **NO**.\n"
            "  • Genuinely ambiguous card (The Moon, The Hanged Man, The Hermit, The High Priestess in some contexts) → **MAYBE**.\n"
            "  Then, in 2-4 short sentences, explain WHY using the canonical meaning above and acknowledge the card's orientation.\n"
        )

    return f"""You are a wise and compassionate tarot reader with deep mystical knowledge.
You read the cards in English with poetic depth and emotional sensitivity.

The seeker has drawn a {SPREAD_NAMES.get(type_tirage, 'tarot spread')}.
{orientation_summary}
{question_block}
Cards drawn:
{cards_text}
{orientation_rules}

Provide a {length} interpretation of this reading.
- If a question was asked, address it directly through the lens of the cards.
- Open with a 2-3 sentence overview of the spread's overall energy (reference the upright/reversed balance).
- Interpret each card in its position, ALWAYS naming its orientation (upright or reversed) and weaving them into a coherent narrative.
- Close with a warm, encouraging message or a call to action.
- Write in a mystical yet accessible tone — poetic but clear.
- Do NOT start with "Sure", "Here is", or "Certainly". Begin the reading immediately.{yesno_instructions}"""


async def generer_interpretation(
    cartes: list[dict],
    type_tirage: str,
    is_premium: bool,
    question: str = "",
) -> AsyncGenerator[str, None]:
    """
    Générateur async SSE — streaming via Groq API.
    """
    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = build_prompt(cartes, type_tirage, is_premium, question)
    max_tokens = 1000 if is_premium else 350

    try:
        stream = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.85,
            stream=True,
        )

        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"

        yield 'data: {"done": true}\n\n'

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
