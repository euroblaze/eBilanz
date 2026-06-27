"""Odoo-Verbindung (Einzelzeile pro Instanz, PRD §4.7)."""
import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OdooConnection(Base):
    __tablename__ = "odoo_connection"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500), default="")
    db: Mapped[str] = mapped_column(String(255), default="")
    username: Mapped[str] = mapped_column(String(255), default="")
    # Hinweis: api_key spaeter im Vault/verschluesselt ablegen (PRD §4.4 Sicherheits-Banner).
    api_key: Mapped[str] = mapped_column(String(500), default="")
    company_id: Mapped[int] = mapped_column(Integer, default=1)
    protocol: Mapped[str] = mapped_column(String(20), default="jsonrpc")  # jsonrpc | xmlrpc
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )

    @property
    def configured(self) -> bool:
        return bool(self.url and self.db)
