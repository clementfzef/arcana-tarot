import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base


class Tirage(Base):
    __tablename__ = "tirages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # '1_carte' | 'oui_non' | 'passe_present_futur' | 'croix_celtique'
    cartes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Exemple de structure cartes :
    # [{"id": 0, "nom": "Le Mat", "position": "présent", "inversee": false, "interpretation": "..."}]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
