"""E-Bilanz-Projekt = 1 Wirtschaftsjahr (WJ) — zentrales Arbeitsobjekt (PRD §0)."""
import datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Wirtschaftsjahr(Base):
    __tablename__ = "wirtschaftsjahr"

    id: Mapped[int] = mapped_column(primary_key=True)
    bezeichnung: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    von: Mapped[datetime.date] = mapped_column(Date)
    bis: Mapped[datetime.date] = mapped_column(Date)
    taxonomie_version: Mapped[str] = mapped_column(String(10))
    taxonomie_label: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40))  # PRD §1.3 Statuswerte
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now
    )
