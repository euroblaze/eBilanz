"""GAAP-Erfassungs-Endpunkte (PRD §3.5). Persistiert erfasste Werte + NIL."""
import copy

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import GaapValue, Wirtschaftsjahr
from libs.ebilanz_demo import GAAP_BESTANDTEILE, GAAP_TREES

router = APIRouter(prefix="/api/gaap", tags=["gaap"])


def _wj(wj_id: int, db: Session) -> Wirtschaftsjahr:
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    return wj


def _overlay(nodes: list[dict], values: dict[str, GaapValue]) -> None:
    """wert_final/nil aus der DB in die Blaetter des Baums einsetzen."""
    for n in nodes:
        if n.get("children"):
            _overlay(n["children"], values)
        else:
            v = values.get(n["id"])
            n["wertFinal"] = v.wert_final if v else None
            n["nil"] = bool(v.nil) if v else False


@router.get("/{wj_id}/{bestandteil}")
def get_gaap(wj_id: int, bestandteil: str, db: Session = Depends(get_db)):
    _wj(wj_id, db)
    if bestandteil not in GAAP_BESTANDTEILE:
        raise HTTPException(404, "Bestandteil unbekannt.")
    tree = copy.deepcopy(GAAP_TREES[bestandteil])
    values = {
        v.position_id: v
        for v in db.scalars(
            select(GaapValue).where(
                GaapValue.wj_id == wj_id, GaapValue.bestandteil == bestandteil
            )
        ).all()
    }
    _overlay(tree, values)
    return {"bestandteil": bestandteil, "nodes": tree}


class GaapEntry(BaseModel):
    position_id: str
    wert_final: float | None = None
    nil: bool = False


class GaapUpdate(BaseModel):
    werte: list[GaapEntry]


@router.put("/{wj_id}/{bestandteil}")
def put_gaap(wj_id: int, bestandteil: str, body: GaapUpdate, db: Session = Depends(get_db)):
    _wj(wj_id, db)
    if bestandteil not in GAAP_BESTANDTEILE:
        raise HTTPException(404, "Bestandteil unbekannt.")
    existing = {
        v.position_id: v
        for v in db.scalars(
            select(GaapValue).where(
                GaapValue.wj_id == wj_id, GaapValue.bestandteil == bestandteil
            )
        ).all()
    }
    for e in body.werte:
        v = existing.get(e.position_id)
        if v is None:
            v = GaapValue(wj_id=wj_id, bestandteil=bestandteil, position_id=e.position_id)
            db.add(v)
        v.wert_final = e.wert_final
        v.nil = e.nil
    db.commit()
    return {"gespeichert": len(body.werte)}
