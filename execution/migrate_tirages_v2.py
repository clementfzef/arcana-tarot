"""
migrate_tirages_v2.py
---------------------
Ajoute les colonnes question, interpretation, expires_at à la table tirages.
Idempotent : peut être exécuté plusieurs fois sans risque.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db import engine


async def migrate():
    print("Connexion à la base de données...")
    async with engine.begin() as conn:
        print("Ajout des colonnes question, interpretation, expires_at...")
        await conn.execute(text("""
            ALTER TABLE tirages
            ADD COLUMN IF NOT EXISTS question TEXT,
            ADD COLUMN IF NOT EXISTS interpretation TEXT,
            ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_tirages_expires_at ON tirages (expires_at)"
        ))
        print("[OK] Colonnes ajoutées")
        print("[OK] Index expires_at créé")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
