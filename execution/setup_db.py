"""
setup_db.py
-----------
Crée toutes les tables PostgreSQL à partir des modèles SQLAlchemy.
À exécuter une seule fois (ou après une modification de schéma).

Usage :
    python execution/setup_db.py
"""

import asyncio
import sys
import os

# Ajouter la racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import engine, Base

# Import des modèles pour que SQLAlchemy les enregistre
from backend.models import User, Tirage, Quota, Card


async def create_tables():
    print("Connexion à la base de données...")
    async with engine.begin() as conn:
        print("Création des tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Tables créées avec succès :")
    for table in Base.metadata.tables.keys():
        print(f"  [OK] {table}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
