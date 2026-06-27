"""Dependency-Injection: DB-Session, Odoo-Client, aktueller Benutzer."""
from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import OdooConnection, User
from app.security import decode_access_token
from libs.odoo_client import OdooClient


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_odoo_connection(db: Session = Depends(get_db)) -> OdooConnection | None:
    return db.scalar(select(OdooConnection).limit(1))


def get_odoo_client(db: Session = Depends(get_db)) -> OdooClient | None:
    """Client aus DB-Zeile bauen; None wenn nicht konfiguriert (-> Demo-Modus)."""
    row = db.scalar(select(OdooConnection).limit(1))
    if not row or not row.configured:
        return None
    return OdooClient(
        url=row.url,
        db=row.db,
        username=row.username,
        api_key=row.api_key,
        company_id=row.company_id,
        protocol=row.protocol,
    )


def get_current_user(
    db: Session = Depends(get_db), authorization: str | None = Header(default=None)
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nicht angemeldet.")
    payload = decode_access_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token ungültig oder abgelaufen.")
    user = db.scalar(select(User).where(User.email == payload.get("sub")))
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzer nicht verfügbar.")
    return user
