import uuid
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 0-77
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    arcane: Mapped[str] = mapped_column(String(20), nullable=False)  # 'majeur' | 'mineur'
    number: Mapped[str] = mapped_column(String(10), nullable=False)
    suit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # coupe, baton, denier, epee
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False)  # ["liberté", "voyage", ...]
    upright: Mapped[str] = mapped_column(String(1000), nullable=False)
    reversed: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
