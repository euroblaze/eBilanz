"""Übermittlung + Protokoll (PRD §3.8/§3.9).

Ohne ECHTE ERiC-Übertragung: erzeugt einen Übermittlungs-Datensatz (Test/Echt).
"""
import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Uebermittlung, Wirtschaftsjahr

router = APIRouter(prefix="/api", tags=["uebermittlung"])


def _serialize(u: Uebermittlung, wj_bez: str) -> dict:
    return {
        "id": u.id,
        "wj": wj_bez,
        "datum": u.datum.isoformat(timespec="seconds"),
        "modus": u.modus,
        "status": u.status,
        "transfer_ticket": u.transfer_ticket,
        "benutzer": u.benutzer,
        "rueckmeldung": u.rueckmeldung,
    }


class SendIn(BaseModel):
    modus: str  # "test" | "echt"
    benutzer: str = "S. Bauer"


@router.post("/uebermittlung/{wj_id}")
def senden(wj_id: int, body: SendIn, db: Session = Depends(get_db)):
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    echt = body.modus == "echt"
    now = datetime.datetime.now()
    ticket = f"TT-{wj.von.year}-{now.strftime('%H%M%S')}"
    u = Uebermittlung(
        wj_id=wj.id,
        datum=now,
        modus="Echt" if echt else "Test",
        status="Echtfall gesendet" if echt else "Testfall gesendet",
        transfer_ticket=ticket,
        benutzer=body.benutzer,
        rueckmeldung="Übermittlung angenommen. Transferticket bestätigt."
        if echt
        else "Verarbeitung erfolgreich (Testmerker gesetzt). Keine Fehler.",
    )
    db.add(u)
    # WJ-Status nach Versand aktualisieren (Lock-Konzept im Frontend).
    wj.status = u.status
    db.commit()
    db.refresh(u)
    return _serialize(u, wj.bezeichnung)


@router.get("/uebermittlungen")
def liste(wj_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Uebermittlung).order_by(Uebermittlung.datum.desc())
    if wj_id is not None:
        stmt = stmt.where(Uebermittlung.wj_id == wj_id)
    rows = list(db.scalars(stmt).all())
    bez = {w.id: w.bezeichnung for w in db.scalars(select(Wirtschaftsjahr)).all()}
    return [_serialize(u, bez.get(u.wj_id, "—")) for u in rows]
