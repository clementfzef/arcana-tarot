"""
Routes d'authentification :
  POST /auth/register  — inscription email + prénom + mot de passe
  POST /auth/login     — connexion, retourne un JWT
  GET  /auth/me        — profil de l'utilisateur connecté
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, field_validator

# Limiter dédié à l'auth — protège contre brute force
limiter = Limiter(key_func=get_remote_address)

from backend.db import get_db
from backend.models.user import User
from backend.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    require_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schémas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    prenom: str
    password: str

    @field_validator("prenom")
    @classmethod
    def prenom_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le prénom ne peut pas être vide")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    prenom: str
    is_premium: bool


# ── Routes ─────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Vérifier si l'email existe déjà
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    user = User(
        email=body.email,
        prenom=body.prenom,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # Pour obtenir l'id avant le commit

    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "prenom": user.prenom,
            "is_premium": user.is_premium,
        },
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "prenom": user.prenom,
            "is_premium": user.is_premium,
        },
    }


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(require_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "prenom": user.prenom,
        "is_premium": user.is_premium,
    }
