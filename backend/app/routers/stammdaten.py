"""Stammdaten-Persistenz (PRD §3.2) — manuelle Felder je WJ speichern/laden."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import StammdatenWert, Wirtschaftsjahr

router = APIRouter(prefix="/api/stammdaten", tags=["stammdaten"])


def _wj(wj_id: int, db: Session) -> Wirtschaftsjahr:
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    return wj


@router.get("/{wj_id}")
def get_stammdaten(wj_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    _wj(wj_id, db)
    rows = db.scalars(select(StammdatenWert).where(StammdatenWert.wj_id == wj_id)).all()
    return {r.feld_key: r.wert for r in rows}


class StammdatenUpdate(BaseModel):
    werte: dict[str, str]


@router.put("/{wj_id}")
def put_stammdaten(wj_id: int, body: StammdatenUpdate, db: Session = Depends(get_db)):
    _wj(wj_id, db)
    existing = {
        r.feld_key: r
        for r in db.scalars(select(StammdatenWert).where(StammdatenWert.wj_id == wj_id)).all()
    }
    for key, value in body.werte.items():
        row = existing.get(key)
        if row is None:
            db.add(StammdatenWert(wj_id=wj_id, feld_key=key, wert=value or ""))
        else:
            row.wert = value or ""
    db.commit()
    return {"gespeichert": len(body.werte)}
