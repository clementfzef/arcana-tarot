# Directive : Site de Tarot Interactif

## Objectif

Créer un site web interactif de tarot, accessible sur internet, responsive mobile/desktop. Les utilisateurs anonymes ont droit à 3 tirages gratuits par jour. Ils peuvent créer un compte (email + prénom) et payer 5€/mois via Stripe pour débloquer les tirages illimités et tous les types de tirage. Les interprétations sont générées dynamiquement par l'API Anthropic.

---

## Stack technique

| Couche | Techno | Hébergement | Coût |
|--------|--------|-------------|------|
| Backend | FastAPI (Python) | Render.com | Gratuit |
| Base de données | PostgreSQL | Supabase | Gratuit |
| Frontend | HTML / CSS / JS | Netlify ou Vercel | Gratuit |
| Paiements | Stripe | — | % commission |
| LLM | Anthropic API | — | Pay per use |

---

## Types de tirages

| Tirage | Cartes | Accès |
|--------|--------|-------|
| 1 carte | 1 | Gratuit (dans la limite quotidienne) |
| Oui / Non | 2 | Premium uniquement |
| Passé / Présent / Futur | 3 | Premium uniquement |
| Croix Celtique | 10 | Premium uniquement |

---

## Modèle d'accès

### Utilisateur anonyme (pas de compte)
- 3 tirages gratuits par jour (toutes cartes confondues)
- Tirage 1 carte uniquement
- Pas d'historique
- Quota basé sur l'IP + cookie de session

### Utilisateur inscrit gratuit
- 3 tirages gratuits par jour
- Tirage 1 carte uniquement
- Historique des 10 derniers tirages visible
- Quota basé sur le compte (plus fiable que l'IP)

### Utilisateur premium (5€/mois via Stripe)
- Tirages illimités
- Tous les types de tirage débloqués
- Historique complet illimité
- Interprétations LLM plus détaillées

---

## Fonctionnalités détaillées

### Authentification
- Inscription : email + prénom (pas de nom complet)
- Pas de mot de passe → magic link par email (plus simple, plus sécurisé)
- Ou mot de passe classique si magic link trop complexe à implémenter en V1
- Pas d'OAuth (Google, etc.) en V1

### Paiement (Stripe)
- Abonnement mensuel : 5€/mois
- Stripe Checkout (hosted page Stripe — pas besoin de gérer la CB nous-mêmes)
- Webhook Stripe pour activer/désactiver le premium en temps réel
- Annulation depuis un portail client Stripe (Stripe Customer Portal)

### Tirages
- Shuffle cryptographique (`secrets.SystemRandom` côté backend)
- Cartes inversées possibles (30% de probabilité par carte)
- Une carte ne peut pas apparaître deux fois dans le même tirage
- Chaque tirage est sauvegardé en base si l'utilisateur est connecté

### Interprétations LLM
- Appel à l'API Anthropic après chaque tirage
- Prompt contextualisé : type de tirage + cartes tirées + positions + sens (endroit/inversé)
- Réponse en streaming (affichage progressif du texte)
- Langue : français
- Anonymes et gratuits : interprétation courte (~100 mots par carte)
- Premium : interprétation longue et détaillée (~300 mots par carte)

### Quota quotidien
- Reset à minuit UTC
- Anonymes : comptage par IP + cookie (best effort)
- Inscrits : comptage en base par user_id + date

### Responsive
- Design mobile-first (priorité téléphone)
- Breakpoints : mobile (<768px), tablette (768–1024px), desktop (>1024px)
- Cartes et animations adaptées au tactile (tap pour retourner)

---

## Architecture backend (FastAPI)

```
backend/
├── main.py                 # Point d'entrée FastAPI
├── routers/
│   ├── auth.py             # Inscription, login, magic link
│   ├── tirages.py          # Logique de tirage, quota, historique
│   ├── stripe_webhooks.py  # Événements Stripe (paiement, annulation)
│   └── cards.py            # Données des cartes (endpoint lecture)
├── models/
│   ├── user.py             # Table users
│   ├── tirage.py           # Table tirages
│   └── quota.py            # Table quotas journaliers
├── services/
│   ├── anthropic.py        # Appel LLM + streaming
│   ├── stripe.py           # Création session, portail client
│   └── shuffle.py          # Algorithme de tirage cryptographique
├── db.py                   # Connexion Supabase / PostgreSQL
├── config.py               # Variables d'environnement
└── requirements.txt
```

---

## Schéma base de données (PostgreSQL)

```sql
-- Utilisateurs
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    prenom TEXT NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tirages sauvegardés
CREATE TABLE tirages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,          -- '1_carte' | 'oui_non' | 'passe_present_futur' | 'croix_celtique'
    cartes JSONB NOT NULL,       -- [{id, nom, position, inversee, interpretation}]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quota journalier (anonymes + inscrits gratuits)
CREATE TABLE quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL si anonyme
    ip TEXT,                     -- pour les anonymes
    date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    UNIQUE(user_id, date),
    UNIQUE(ip, date)
);
```

---

## Variables d'environnement (.env)

```
# Anthropic
ANTHROPIC_API_KEY=

# Supabase / PostgreSQL
DATABASE_URL=postgresql://...

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=               # ID du prix premium 5€/mois

# App
SECRET_KEY=                    # Pour signer les JWT/sessions
FRONTEND_URL=                  # URL du frontend (CORS)
```

---

## Scripts d'exécution

| Script | Rôle |
|--------|------|
| `execution/setup_db.py` | Crée les tables en base depuis le schéma SQL |
| `execution/seed_cards.py` | Insère les 78 cartes de tarot en base ou génère `cards.js` |
| `execution/test_anthropic.py` | Teste l'appel LLM avec un tirage exemple |
| `execution/test_stripe.py` | Vérifie la config Stripe (prix, webhook) |

---

## Ordre de construction

1. **Base de données** — schéma + seed des cartes
2. **Backend FastAPI** — routes auth, tirages, quota, stripe webhooks
3. **Intégration LLM** — streaming Anthropic
4. **Frontend** — HTML/CSS/JS responsive, mobile-first
5. **Stripe Checkout** — paiement + portail client
6. **Déploiement** — Render (backend) + Netlify (frontend) + Supabase (DB)

---

## Définition du succès

- [ ] Un anonyme peut tirer 3 cartes (1 carte) puis est bloqué jusqu'au lendemain
- [ ] Un inscrit gratuit voit son quota en base, pas juste en cookie
- [ ] Un premium peut faire tous les types de tirage sans limite
- [ ] Le paiement Stripe fonctionne en mode test
- [ ] Le webhook Stripe active/désactive le premium automatiquement
- [ ] L'interprétation s'affiche en streaming (lettre par lettre)
- [ ] Le site est lisible et utilisable sur un iPhone SE (375px)
