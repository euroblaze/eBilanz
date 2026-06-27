"""Finanzaemter-Optionen — kanonische Quelle fuer die Stammdaten-Auswahl (PRD §3.2).

Liefert die 16 Bundeslaender und je Bundesland die Finanzaemter (Name + BUFA),
fuer die abhaengige Auswahl: zuerst Bundesland, dann Finanzamt.
"""
from fastapi import APIRouter

from app.constants.finanzaemter import BUNDESLAENDER, FINANZAEMTER_BY_BUNDESLAND

router = APIRouter(prefix="/api/finanzaemter", tags=["finanzaemter"])


@router.get("")
def finanzaemter():
    return {
        "bundeslaender": BUNDESLAENDER,
        "nach_bundesland": FINANZAEMTER_BY_BUNDESLAND,
    }
