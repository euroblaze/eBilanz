from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db, get_odoo_connection
from app.models import OdooConnection

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(
    db: Session = Depends(get_db),
    odoo: OdooConnection | None = Depends(get_odoo_connection),
):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    konfiguriert = bool(odoo and odoo.configured)
    return {
        "status": "ok",
        "env": settings.app_env,
        "db": db_ok,
        "odoo_configured": konfiguriert,
        "odoo_db": odoo.db if konfiguriert else None,
    }
