"""Salden-Snapshot: zuletzt übernommener Import je WJ (für Diff, PRD §3.3)."""
from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SaldoSnapshot(Base):
    __tablename__ = "saldo_snapshot"
    __table_args__ = (UniqueConstraint("wj_id", "code", name="uq_snapshot_wj_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200), default="")
    account_type: Mapped[str] = mapped_column(String(80), default="")
    saldo: Mapped[float] = mapped_column(Float, default=0.0)
    soll_haben: Mapped[str] = mapped_column(String(2), default="S")
    buchungen: Mapped[int] = mapped_column(Integer, default=0)
