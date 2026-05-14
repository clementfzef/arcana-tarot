"""
Service Anthropic — génération d'interprétation en streaming (SSE).
"""

import json
from typing import AsyncGenerator

import anthropic

from backend.config import get_settings

settings = get_settings()
client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SPREAD_NAMES = {
    "1_carte": "Single Card",
    "oui_non": "Yes / No",
    "passe_present_futur": "Past / Present / Future",
    "croix_celtique": "Celtic Cross",
}


def build_prompt(cartes: list[dict], type_tirage: str, is_premium: bool, question: str = "") -> str:
    length = "detailed (approximately 250 words per card)" if is_premium else "concise (approximately 80 words per card)"

    cards_text = "\n".join([
        f"- Position \"{c['position']}\": {c['nom']}"
        f"{' (reversed)' if c.get('inversee') else ''}"
        f" — keywords: {', '.join(c.get('keywords', []))}"
        for c in cartes
    ])

    question_block = f'\nThe seeker\'s question: "{question}"\n' if question.strip() else ""

    return f"""You are an expert and compassionate tarot reader. You read the cards in English with depth and sensitivity.

The user has just performed a {SPREAD_NAMES.get(type_tirage, 'tarot spread')}.
{question_block}
Cards drawn:
{cards_text}

Give a {length} interpretation of this reading.
- If a question was asked, address it directly through the lens of the cards.
- Begin with a 2-3 sentence overview of the spread as a whole.
- Then interpret each card in its position, taking the overall context into account.
- Close with an encouraging or guiding message.
- Use a warm, poetic yet accessible tone.
- Do not start with "Sure" or "Here is". Dive directly into the reading.
"""


async def generer_interpretation(
    cartes: list[dict],
    type_tirage: str,
    is_premium: bool,
    question: str = "",
) -> AsyncGenerator[str, None]:
    """
    Générateur async SSE — chaque chunk est un événement `data: ...`.
    Le frontend lit ces événements et les affiche progressivement.
    """
    prompt = build_prompt(cartes, type_tirage, is_premium, question)
    model = "claude-opus-4-5" if is_premium else "claude-haiku-4-5"
    max_tokens = 1500 if is_premium else 500

    try:
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                # Format SSE : data: <json>\n\n
                payload = json.dumps({"token": text})
                yield f"data: {payload}\n\n"

        # Signal de fin
        yield "data: {\"done\": true}\n\n"

    except anthropic.APIError as e:
        error_payload = json.dumps({"error": str(e)})
        yield f"data: {error_payload}\n\n"
