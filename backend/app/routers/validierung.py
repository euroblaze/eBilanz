"""Validierung (PRD §3.7) — berechnete Prüfmeldungen aus erfasstem Stand.

Ohne ECHTE ERiC-Bibliothek: Mussfeld-/Mapping-Prüfungen aus den persistierten Daten.
"""
import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import GaapValue, MappingEntry, Wirtschaftsjahr
from libs.ebilanz_demo import GAAP_BESTANDTEILE, gaap_leaf_ids

router = APIRouter(prefix="/api/validierung", tags=["validierung"])


@router.post("/{wj_id}")
def pruefen(wj_id: int, db: Session = Depends(get_db)):
    if db.get(Wirtschaftsjahr, wj_id) is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")

    meldungen: list[dict] = []
    n = 0

    # 1) GAAP-Mussfelder ohne Wert und ohne NIL -> Fehler
    for bestandteil in GAAP_BESTANDTEILE:
        leaves = [leaf for leaf in gaap_leaf_ids(bestandteil) if leaf["feldtyp"] == "Mussfeld"]
        if not leaves:
            continue
        values = {
            v.position_id: v
            for v in db.scalars(
                select(GaapValue).where(
                    GaapValue.wj_id == wj_id, GaapValue.bestandteil == bestandteil
                )
            ).all()
        }
        for leaf in leaves:
            v = values.get(leaf["id"])
            if v is None or (v.wert_final is None and not v.nil):
                n += 1
                meldungen.append({
                    "id": f"v{n}", "schwere": "Fehler", "code": "ERIC-2010",
                    "position": f"{bestandteil} › {leaf['label']}",
                    "meldung": "Mussfeld ohne Wert und ohne NIL-Kennzeichen.",
                    "route": f"/gaap/{bestandteil}",
                })

    # 2) Nicht zugeordnete Konten -> Hinweis
    offen = db.scalar(
        select(MappingEntry).where(
            MappingEntry.wj_id == wj_id, MappingEntry.status == "nicht zugeordnet"
        )
    )
    if offen is not None:
        n += 1
        meldungen.append({
            "id": f"v{n}", "schwere": "Hinweis", "code": "ERIC-7001",
            "position": "Konten-Mapping",
            "meldung": "Es bestehen noch nicht zugeordnete Konten.",
            "route": "/mapping",
        })

    fehler = sum(1 for m in meldungen if m["schwere"] == "Fehler")
    hinweis = sum(1 for m in meldungen if m["schwere"] == "Hinweis")
    ampel = "danger" if fehler else "warning" if hinweis else "success"
    return {
        "ampel": ampel,
        "fehler": fehler,
        "hinweis": hinweis,
        "geprueft_am": datetime.datetime.now().isoformat(timespec="seconds"),
        "meldungen": meldungen,
    }
