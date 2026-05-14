"""
Service Gemini — génération d'interprétation tarot en streaming (SSE).
Modèle : gemini-2.0-flash (1500 req/jour gratuites)
"""

import json
from typing import AsyncGenerator
from google import genai
from google.genai import types

from backend.config import get_settings

settings = get_settings()

SPREAD_NAMES = {
    "1_carte":             "Single Card",
    "oui_non":             "Yes / No",
    "passe_present_futur": "Past / Present / Future",
    "croix_celtique":      "Celtic Cross",
}


def build_prompt(cartes: list[dict], type_tirage: str, is_premium: bool, question: str = "") -> str:
    length = "detailed and rich (approximately 250 words per card)" if is_premium \
             else "concise and evocative (approximately 80 words per card)"

    cards_text = "\n".join([
        f"- Position \"{c['position']}\": {c['nom']}"
        f"{' (reversed)' if c.get('inversee') else ''}"
        f" — keywords: {', '.join(c.get('keywords', []))}"
        for c in cartes
    ])

    question_block = f'\nThe seeker\'s question: "{question}"\n' if question.strip() else ""

    return f"""You are a wise and compassionate tarot reader with deep mystical knowledge.
You read the cards in English with poetic depth and emotional sensitivity.

The seeker has drawn a {SPREAD_NAMES.get(type_tirage, 'tarot spread')}.
{question_block}
Cards drawn:
{cards_text}

Provide a {length} interpretation of this reading.
- If a question was asked, answer it directly through the lens of the cards.
- Open with a 2-3 sentence overview of the energy of the spread.
- Interpret each card in its position, weaving them into a coherent narrative.
- Close with a warm, encouraging message or a call to action.
- Write in a mystical yet accessible tone — poetic but clear.
- Do NOT start with "Sure", "Here is", "Certainly" or similar. Begin the reading immediately.
"""


async def generer_interpretation(
    cartes: list[dict],
    type_tirage: str,
    is_premium: bool,
    question: str = "",
) -> AsyncGenerator[str, None]:
    """
    Générateur async SSE utilisant Gemini 2.0 Flash en streaming.
    """
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = build_prompt(cartes, type_tirage, is_premium, question)
    max_tokens = 1200 if is_premium else 400

    try:
        async for chunk in await client.aio.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.85,
                candidate_count=1,
            ),
        ):
            if chunk.text:
                payload = json.dumps({"token": chunk.text})
                yield f"data: {payload}\n\n"

        yield 'data: {"done": true}\n\n'

    except Exception as e:
        error_payload = json.dumps({"error": str(e)})
        yield f"data: {error_payload}\n\n"
