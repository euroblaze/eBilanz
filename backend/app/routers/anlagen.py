"""Anlagenbuchhaltung — Asset-Register + Sonderposten je WJ (PRD §3.5).

Liefert die in der DB gefuehrten Anlagegueter (AHK, kum. Abschreibung, Buchwert)
und Sonderposten (investive Zuschuesse). Quelle des Anlagenspiegels.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Anlage, AnlagenSonderposten, Wirtschaftsjahr

router = APIRouter(prefix="/api/anlagen", tags=["anlagen"])


@router.get("/{wj_id}")
def anlagen(wj_id: int, db: Session = Depends(get_db)):
    if db.get(Wirtschaftsjahr, wj_id) is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")

    assets = db.scalars(
        select(Anlage).where(Anlage.wj_id == wj_id).order_by(Anlage.klasse_id, Anlage.id)
    ).all()
    sopos = db.scalars(
        select(AnlagenSonderposten)
        .where(AnlagenSonderposten.wj_id == wj_id)
        .order_by(AnlagenSonderposten.id)
    ).all()

    anlagen_out = [
        {
            "id": a.id,
            "klasse_id": a.klasse_id,
            "klasse_label": a.klasse_label,
            "bezeichnung": a.bezeichnung,
            "ahk": a.ahk,
            "kum_abschreibung": a.kum_abschreibung,
            "buchwert": a.ahk + a.kum_abschreibung,
            "anschaffungsjahr": a.anschaffungsjahr,
            "nutzungsdauer_jahre": a.nutzungsdauer_jahre,
        }
        for a in assets
    ]
    sopo_out = [
        {
            "id": s.id,
            "anlage_id": s.anlage_id,
            "bezeichnung": s.bezeichnung,
            "geber": s.geber,
            "stand_anfang": s.stand_anfang,
            "zugang": s.zugang,
            "aufloesung": s.aufloesung,
            "stand_ende": s.stand_anfang + s.zugang + s.aufloesung,
        }
        for s in sopos
    ]
    summen = {
        "ahk": sum(a.ahk for a in assets),
        "kum_abschreibung": sum(a.kum_abschreibung for a in assets),
        "buchwert": sum(a.ahk + a.kum_abschreibung for a in assets),
        "sonderposten_stand_ende": sum(
            s.stand_anfang + s.zugang + s.aufloesung for s in sopos
        ),
    }
    return {"wj_id": wj_id, "anlagen": anlagen_out, "sonderposten": sopo_out, "summen": summen}
