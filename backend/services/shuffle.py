"""
Service de tirage cryptographique.
Utilise secrets.SystemRandom pour un vrai aléatoire (pas random.shuffle).
"""

import secrets
from typing import Literal

TirageType = Literal["1_carte", "oui_non", "passe_present_futur", "croix_celtique"]

# Positions pour chaque type de tirage
POSITIONS = {
    "1_carte": ["Card of the Moment"],
    "oui_non": ["The Answer"],
    "passe_present_futur": ["Past", "Present", "Future"],
    "croix_celtique": [
        "Heart of the Matter",
        "The Challenge",
        "The Past",
        "The Future",
        "The Outcome",
    ],
}

NB_CARTES = {
    "1_carte": 1,
    "oui_non": 1,
    "passe_present_futur": 3,
    "croix_celtique": 5,
}

# Cartes réservées aux premium
PREMIUM_TIRAGES = {"oui_non", "passe_present_futur", "croix_celtique"}

rng = secrets.SystemRandom()


def tirer_cartes(type_tirage: TirageType, all_card_ids: list[int]) -> list[dict]:
    """
    Tire N cartes uniques aléatoirement depuis all_card_ids.
    Retourne une liste de dicts avec id, position et inversee.
    """
    nb = NB_CARTES[type_tirage]
    positions = POSITIONS[type_tirage]

    if len(all_card_ids) < nb:
        raise ValueError(f"Pas assez de cartes en base ({len(all_card_ids)} < {nb})")

    # Fisher-Yates partiel — on ne mélange que ce dont on a besoin
    pool = list(all_card_ids)
    drawn = []
    for i in range(nb):
        j = rng.randint(i, len(pool) - 1)
        pool[i], pool[j] = pool[j], pool[i]
        inversee = rng.random() < 0.30  # 30% de chance d'être inversée
        drawn.append({
            "card_id": pool[i],
            "position": positions[i],
            "inversee": inversee,
        })

    return drawn
