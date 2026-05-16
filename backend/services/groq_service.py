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

    # Special instructions for Yes/No spreads — must give a clear verdict
    yesno_instructions = ""
    if type_tirage == "oui_non":
        yesno_instructions = (
            "\n- This is a YES / NO reading. You MUST open with a clear, single-word verdict on its own line:\n"
            "  • If the card is upright and its energy is favorable to the question → answer **YES**.\n"
            "  • If the card is reversed or its energy is unfavorable → answer **NO**.\n"
            "  • If the card is genuinely ambiguous (The Moon, The Hanged Man, etc.) → answer **MAYBE**.\n"
            "  Then, in 2-4 short sentences, explain WHY the card gives this answer, with nuance.\n"
        )

    return f"""You are a wise and compassionate tarot reader with deep mystical knowledge.
You read the cards in English with poetic depth and emotional sensitivity.

The seeker has drawn a {SPREAD_NAMES.get(type_tirage, 'tarot spread')}.
{question_block}
Cards drawn:
{cards_text}

Provide a {length} interpretation of this reading.
- If a question was asked, address it directly through the lens of the cards.
- Open with a 2-3 sentence overview of the energy of the spread.
- Interpret each card in its position, weaving them into a coherent narrative.
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
