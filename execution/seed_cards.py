"""
seed_cards.py
-------------
Inserts the 22 major arcana tarot cards into the database (English).

Usage:
    python execution/seed_cards.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db import engine, AsyncSessionLocal
from backend.models.card import Card

# ─────────────────────────────────────────────────────────
# CARD DATA — 22 MAJOR ARCANA (English)
# ─────────────────────────────────────────────────────────

MAJOR_ARCANA = [
    {
        "id": 0, "name": "The Fool", "arcane": "major", "number": "0", "suit": None,
        "keywords": ["freedom", "new beginning", "spontaneity", "adventure"],
        "upright": "A new journey begins. The Fool invites you to trust the path, to leap into the unknown without fear of judgment. Now is the time to take that first step.",
        "reversed": "Recklessness, lack of direction. You are avoiding an important decision or diving into something without considering the risks.",
    },
    {
        "id": 1, "name": "The Magician", "arcane": "major", "number": "I", "suit": None,
        "keywords": ["willpower", "skill", "action", "manifestation"],
        "upright": "You have all the tools you need. The Magician symbolizes the power to turn ideas into reality through focus, willpower, and intentional action.",
        "reversed": "Manipulation, misuse of talent. Be careful not to scatter your energy or use your power dishonestly.",
    },
    {
        "id": 2, "name": "The High Priestess", "arcane": "major", "number": "II", "suit": None,
        "keywords": ["intuition", "wisdom", "mystery", "patience"],
        "upright": "Trust your intuition. The High Priestess calls for introspection and inner stillness. The answers you seek are already within you.",
        "reversed": "Hidden secrets, blocked intuition. You are ignoring your inner voice or refusing to acknowledge an uncomfortable truth.",
    },
    {
        "id": 3, "name": "The Empress", "arcane": "major", "number": "III", "suit": None,
        "keywords": ["abundance", "femininity", "nature", "creation"],
        "upright": "A time of fertility and abundance. The Empress brings creativity, material and emotional prosperity. Nurture yourself and those you love.",
        "reversed": "Creative block, dependence, overprotection. You may be smothering something or someone, or neglecting your own needs.",
    },
    {
        "id": 4, "name": "The Emperor", "arcane": "major", "number": "IV", "suit": None,
        "keywords": ["authority", "structure", "stability", "leadership"],
        "upright": "It is time to establish order and structure. The Emperor represents leadership, discipline, and the ability to build something lasting.",
        "reversed": "Tyranny, rigidity, abuse of power. You may be too controlling or you are enduring oppressive authority. Seek balance.",
    },
    {
        "id": 5, "name": "The Hierophant", "arcane": "major", "number": "V", "suit": None,
        "keywords": ["tradition", "guidance", "belief", "teaching"],
        "upright": "Seek a mentor or a tradition that guides you. The Hierophant represents the transmission of knowledge, moral values, and spiritual wisdom.",
        "reversed": "Dogmatism, rebellion against convention. You feel stifled by rigid rules or are rejecting useful guidance.",
    },
    {
        "id": 6, "name": "The Lovers", "arcane": "major", "number": "VI", "suit": None,
        "keywords": ["choice", "love", "values", "alignment"],
        "upright": "An important choice presents itself. The Lovers speak of alignment with your deepest values, a harmonious relationship, or a heartfelt decision.",
        "reversed": "Imbalance, wrong choices, conflict of values. You are torn between two paths or avoiding a necessary decision.",
    },
    {
        "id": 7, "name": "The Chariot", "arcane": "major", "number": "VII", "suit": None,
        "keywords": ["victory", "mastery", "determination", "movement"],
        "upright": "Move forward with confidence. The Chariot announces victory through discipline and self-mastery. You have the strength to overcome any obstacle.",
        "reversed": "Loss of control, aggression, powerlessness. You may be charging in the wrong direction or stuck without being able to move forward.",
    },
    {
        "id": 8, "name": "Strength", "arcane": "major", "number": "VIII", "suit": None,
        "keywords": ["courage", "gentleness", "inner mastery", "patience"],
        "upright": "Your true strength comes from within. Strength invites you to tame your fears and instincts with gentleness rather than force. You can overcome anything.",
        "reversed": "Self-doubt, self-sabotage. You are letting your fears dominate you or using your strength in a destructive way.",
    },
    {
        "id": 9, "name": "The Hermit", "arcane": "major", "number": "IX", "suit": None,
        "keywords": ["solitude", "inner search", "wisdom", "retreat"],
        "upright": "It is time to withdraw and reflect. The Hermit invites meaningful solitude, deep introspection, and the search for your own inner light.",
        "reversed": "Excessive isolation, refusing help. You are cutting yourself off from the world in a harmful way or rejecting others' guidance.",
    },
    {
        "id": 10, "name": "Wheel of Fortune", "arcane": "major", "number": "X", "suit": None,
        "keywords": ["luck", "cycles", "destiny", "change"],
        "upright": "Luck is turning in your favor. The Wheel of Fortune signals a shift in cycles, an opportunity to seize. Things are naturally evolving.",
        "reversed": "Bad luck, resistance to change. You are fighting against a natural cycle or going through a difficult period. Accept the flow of life.",
    },
    {
        "id": 11, "name": "Justice", "arcane": "major", "number": "XI", "suit": None,
        "keywords": ["fairness", "truth", "cause and effect", "decision"],
        "upright": "A fair outcome will be reached. Justice reminds you that every action has consequences. Act with integrity and truth will prevail.",
        "reversed": "Injustice, imbalance, avoiding responsibility. You are refusing to face the consequences of your actions or suffering an unfair situation.",
    },
    {
        "id": 12, "name": "The Hanged Man", "arcane": "major", "number": "XII", "suit": None,
        "keywords": ["suspension", "surrender", "sacrifice", "new perspective"],
        "upright": "It is time to see everything differently. The Hanged Man invites you to accept a pause or a voluntary sacrifice to gain a fresh perspective.",
        "reversed": "Useless resistance, futile sacrifice, stagnation. You are clinging to something that no longer serves you. Let go.",
    },
    {
        "id": 13, "name": "Death", "arcane": "major", "number": "XIII", "suit": None,
        "keywords": ["transformation", "ending", "transition", "renewal"],
        "upright": "A necessary ending for a new beginning. Death is not to be feared — it announces a profound and liberating transformation.",
        "reversed": "Resistance to change, stagnation, fear of letting go. You are clinging to a dead situation. The transition is inevitable.",
    },
    {
        "id": 14, "name": "Temperance", "arcane": "major", "number": "XIV", "suit": None,
        "keywords": ["balance", "moderation", "patience", "harmony"],
        "upright": "Find your balance. Temperance invites patience, harmony, and the wisdom of the middle path. Everything comes to those who wait.",
        "reversed": "Excess, imbalance, impatience. You are overindulging in some area of your life. Find your way back to moderation.",
    },
    {
        "id": 15, "name": "The Devil", "arcane": "major", "number": "XV", "suit": None,
        "keywords": ["attachment", "addiction", "materialism", "illusion"],
        "upright": "You are bound to something or someone. The Devil reveals your dependencies and attachments. Awareness is the first step toward freedom.",
        "reversed": "Liberation, breaking free. You are beginning to release a dependency or illusion. Keep going in this direction.",
    },
    {
        "id": 16, "name": "The Tower", "arcane": "major", "number": "XVI", "suit": None,
        "keywords": ["upheaval", "revelation", "chaos", "sudden awakening"],
        "upright": "An unexpected upheaval is coming. The Tower destroys what was built on false foundations. It is painful but necessary to rebuild on solid ground.",
        "reversed": "Avoiding a crisis, resisting the inevitable. The chaos is coming regardless — resistance only makes things worse.",
    },
    {
        "id": 17, "name": "The Star", "arcane": "major", "number": "XVII", "suit": None,
        "keywords": ["hope", "inspiration", "healing", "faith"],
        "upright": "Hope is here. The Star brings renewal, healing, and faith in the future after a difficult period. You are on the right path.",
        "reversed": "Despair, lack of faith, pessimism. You are struggling to see the light at the end of the tunnel. Reconnect with your dreams.",
    },
    {
        "id": 18, "name": "The Moon", "arcane": "major", "number": "XVIII", "suit": None,
        "keywords": ["illusion", "fears", "the unconscious", "confusion"],
        "upright": "Something is hidden or not what it seems. The Moon illuminates fears, illusions, and shadow areas. Trust your instincts.",
        "reversed": "Illusions are fading, clarity returns. The confusion is lifting. You are beginning to see reality as it truly is.",
    },
    {
        "id": 19, "name": "The Sun", "arcane": "major", "number": "XIX", "suit": None,
        "keywords": ["joy", "success", "vitality", "clarity"],
        "upright": "Success, joy, and clarity. The Sun is one of the most positive cards in the tarot. It announces achievement, fulfillment, and a radiant period ahead.",
        "reversed": "Joy temporarily clouded, lack of confidence. The positive energy is there but something is blocking it. Persevere.",
    },
    {
        "id": 20, "name": "Judgement", "arcane": "major", "number": "XX", "suit": None,
        "keywords": ["awakening", "rebirth", "absolution", "calling"],
        "upright": "An inner call to awaken. Judgement invites reflection, forgiveness, and answering a deep vocation. A rebirth is possible.",
        "reversed": "Refusing the awakening, regrets, harsh self-judgment. You are being too hard on yourself or resisting a necessary change.",
    },
    {
        "id": 21, "name": "The World", "arcane": "major", "number": "XXI", "suit": None,
        "keywords": ["completion", "integration", "wholeness", "journey"],
        "upright": "Total fulfillment. The World announces the successful end of a cycle, the integration of all experiences, and a deep sense of wholeness. All is accomplished.",
        "reversed": "Incompletion, lack of closure. You are close to the finish line but something remains to be done. Do not stop now.",
    },
]

ALL_CARDS = MAJOR_ARCANA


# ─────────────────────────────────────────────────────────
# INSERT INTO DATABASE
# ─────────────────────────────────────────────────────────

async def seed():
    print(f"Inserting {len(ALL_CARDS)} cards into the database...")
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM cards"))

        for card_data in ALL_CARDS:
            card = Card(**card_data)
            session.add(card)

        await session.commit()

    print(f"  [OK] {len(MAJOR_ARCANA)} major arcana inserted")
    print("Seed complete.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
