"""Stammdaten — persistierte manuelle Felder je WJ (Key-Value, PRD §3.2)."""
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StammdatenWert(Base):
    __tablename__ = "stammdaten_wert"
    __table_args__ = (UniqueConstraint("wj_id", "feld_key", name="uq_stammdaten_wj_feld"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    feld_key: Mapped[str] = mapped_column(String(60))
    wert: Mapped[str] = mapped_column(Text, default="")
