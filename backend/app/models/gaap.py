"""GAAP-Erfassungswerte: erfasster Wert + NIL je Position, WJ und Bestandteil (PRD §3.5)."""
from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GaapValue(Base):
    __tablename__ = "gaap_value"
    __table_args__ = (
        UniqueConstraint("wj_id", "bestandteil", "position_id", name="uq_gaap_pos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    wj_id: Mapped[int] = mapped_column(ForeignKey("wirtschaftsjahr.id"), index=True)
    bestandteil: Mapped[str] = mapped_column(String(40))
    position_id: Mapped[str] = mapped_column(String(60))
    wert_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    nil: Mapped[bool] = mapped_column(Boolean, default=False)
