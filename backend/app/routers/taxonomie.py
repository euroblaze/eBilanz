"""Taxonomie-Optionen — kanonische Quelle fuer die Stammdaten-Auswahl (PRD §3.2)."""
from fastapi import APIRouter

from app.config import settings
from app.constants.taxonomie import TAXONOMIE_ARTEN, TAXONOMIE_VERSIONEN

router = APIRouter(prefix="/api/taxonomien", tags=["taxonomie"])


@router.get("")
def taxonomien():
    return {
        "versionen": TAXONOMIE_VERSIONEN,
        "arten": TAXONOMIE_ARTEN,
        "default": settings.default_taxonomie_art,
    }
