"""GAAP-Erfassungs-Endpunkte (PRD §3.5). Persistiert erfasste Werte + NIL."""
import copy

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db, get_odoo_client
from app.models import Anlage, AnlagenSonderposten, GaapValue, Wirtschaftsjahr
from libs.ebilanz_demo import (
    GAAP_BESTANDTEILE,
    GAAP_TREES,
    build_anlagenspiegel_tree,
)
from libs.odoo_client import OdooClient, OdooError

router = APIRouter(prefix="/api/gaap", tags=["gaap"])


def _asset_klasse(name: str) -> str:
    """Odoo-Anlage anhand des Namens einer Anlagenspiegel-Klasse zuordnen."""
    n = (name or "").lower()
    if any(k in n for k in ("bus", "omnibus", "fahrzeug", "kfz", "pkw", "lkw")):
        return "fahrz"
    if any(k in n for k in ("grundstück", "grundstueck", "gebäude", "gebaeude", "bauten", "halle", "immobil")):
        return "grund"
    if any(k in n for k in ("software", "lizenz", "immateriell")):
        return "immat"
    if any(k in n for k in ("im bau", "ladeinfra")):
        return "aib"
    if any(k in n for k in ("ausstattung", "büro", "buero", "geschäfts", "it-")):
        return "bga"
    return "tech"


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
def get_gaap(
    wj_id: int,
    bestandteil: str,
    db: Session = Depends(get_db),
    client: OdooClient | None = Depends(get_odoo_client),
):
    _wj(wj_id, db)
    if bestandteil not in GAAP_BESTANDTEILE:
        raise HTTPException(404, "Bestandteil unbekannt.")
    if bestandteil == "anlagenspiegel":
        sopos = db.scalars(
            select(AnlagenSonderposten).where(AnlagenSonderposten.wj_id == wj_id)
        ).all()
        # Bevorzugt: echte Odoo-Anlagen (account.asset); Fallback: DB-Register; dann Konstante.
        odoo_assets = None
        if client is not None:
            try:
                odoo_assets = [
                    {
                        "klasse_id": _asset_klasse(a["name"]),
                        "ahk": a["ahk"],
                        "kum_abschreibung": a["kum_abschreibung"],
                    }
                    for a in client.get_assets()
                ]
            except OdooError:
                odoo_assets = None
        if odoo_assets:
            tree = build_anlagenspiegel_tree(odoo_assets, sopos)
        else:
            assets = db.scalars(select(Anlage).where(Anlage.wj_id == wj_id)).all()
            tree = (
                build_anlagenspiegel_tree(assets, sopos)
                if (assets or sopos)
                else copy.deepcopy(GAAP_TREES[bestandteil])
            )
    else:
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
