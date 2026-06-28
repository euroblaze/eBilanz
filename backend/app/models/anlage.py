"""Anlagenbuchhaltung: Anlagegueter (Asset-Register) + Sonderposten je WJ.

Normalisierte Quelle fuer den Anlagenspiegel (PRD §3.5). Der GAAP-Bestandteil
'anlagenspiegel' wird aus diesen Zeilen aggregiert (AHK + kum. Abschreibung =
Buchwert je Klasse; Sonderposten-Entwicklung).
"""
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Anlage(Base):
    """Ein Anlagegut (Wirtschaftsgut) je Wirtschaftsjahr."""

    __tablename__ = "anlage"

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    # Anlageklasse (immat|grund|tech|fahrz|bga|aib) -> Anlagenspiegel-Position.
    klasse_id: Mapped[str] = mapped_column(String(20), index=True)
    klasse_label: Mapped[str] = mapped_column(String(120))
    bezeichnung: Mapped[str] = mapped_column(String(200))
    ahk: Mapped[float] = mapped_column(Float, default=0.0)  # Anschaffungs-/Herstellungskosten
    kum_abschreibung: Mapped[float] = mapped_column(Float, default=0.0)  # negativ
    anschaffungsjahr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nutzungsdauer_jahre: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AnlagenSonderposten(Base):
    """Investiver Zuschuss (Sonderposten); mehrere je Wirtschaftsgut moeglich."""

    __tablename__ = "anlagen_sonderposten"

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    anlage_id: Mapped[int | None] = mapped_column(ForeignKey("anlage.id"), nullable=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    geber: Mapped[str] = mapped_column(String(40), default="")  # Bund|Land|Aufgabenträger
    stand_anfang: Mapped[float] = mapped_column(Float, default=0.0)
    zugang: Mapped[float] = mapped_column(Float, default=0.0)
    aufloesung: Mapped[float] = mapped_column(Float, default=0.0)  # negativ
