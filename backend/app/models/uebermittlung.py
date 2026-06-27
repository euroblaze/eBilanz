"""Übermittlungen / Protokoll (PRD §3.8/§3.9)."""
import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Uebermittlung(Base):
    __tablename__ = "uebermittlung"

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    datum: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    modus: Mapped[str] = mapped_column(String(10))  # Test | Echt
    status: Mapped[str] = mapped_column(String(40))
    transfer_ticket: Mapped[str] = mapped_column(String(40), default="—")
    benutzer: Mapped[str] = mapped_column(String(120), default="")
    rueckmeldung: Mapped[str] = mapped_column(Text, default="")
