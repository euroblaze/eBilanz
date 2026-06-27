"""Konten-Mapping: ein Eintrag je Konto und WJ (PRD §3.4)."""
from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MappingEntry(Base):
    __tablename__ = "mapping_entry"
    __table_args__ = (UniqueConstraint("wj_id", "account_key", name="uq_mapping_wj_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    account_key: Mapped[str] = mapped_column(String(40))  # stabiler Schluessel je Konto
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    saldo: Mapped[float] = mapped_column(Float, default=0.0)
    account_type: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(30), default="nicht zugeordnet")
    position_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    position_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    suggestion_position_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    suggestion_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    suggestion_confidence: Mapped[int] = mapped_column(Integer, default=0)
