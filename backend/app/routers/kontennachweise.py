"""Kontennachweise (PRD §3.6) — Gruppen je Taxonomie-Position + Einzelbuchungen."""
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import MappingEntry, Wirtschaftsjahr
from app.routers.mapping import _seed_if_empty

router = APIRouter(prefix="/api/kontennachweise", tags=["kontennachweise"])


@router.get("/{wj_id}")
def get_kontennachweise(wj_id: int, db: Session = Depends(get_db)):
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    entries = _seed_if_empty(wj, db)
    groups: dict[str, dict] = {}
    for e in entries:
        pid = e.position_id or e.suggestion_position_id or "ohne"
        label = e.position_label or e.suggestion_label or "Ohne Zuordnung"
        g = groups.setdefault(pid, {"label": label, "konten": [], "alle_zugeordnet": True})
        g["konten"].append({"code": e.code, "name": e.name, "saldo": e.saldo})
        if not e.position_id:
            g["alle_zugeordnet"] = False
    return [
        {
            "id": pid,
            "label": g["label"],
            "status": "vollständig" if g["alle_zugeordnet"] else "fehlt",
            "konten": g["konten"],
        }
        for pid, g in groups.items()
    ]


@router.get("/{wj_id}/buchungen")
def get_buchungen(wj_id: int, konto: str = Query(...), db: Session = Depends(get_db)):
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    # Deterministische Demo-Einzelbuchungen (account.move.line folgt mit Live-Odoo).
    # Anzahl variiert je Konto (deterministisch -> bei erneutem Klick stabil).
    seed = int(konto) if konto.isdigit() else (abs(hash(konto)) % 9999)
    rng = random.Random(seed)
    jahr = wj.von.year
    count = rng.randint(1, 12)
    # Betragsgroessenordnung variiert je Konto (deterministisch): manche Konten
    # zeigen kleine Belege, andere grosse.
    hoechst = rng.uniform(800, 500000)
    niedrigst = hoechst * rng.uniform(0.01, 0.25)
    out = []
    for _ in range(count):
        out.append({
            "datum": f"{jahr}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            "beleg": f"RE-{rng.randint(1000, 9999)}",
            "text": ("Zugang" if rng.random() > 0.4 else "Abgang") + f" Konto {konto}",
            "betrag": round(rng.uniform(niedrigst, hoechst), 2),
        })
    out.sort(key=lambda b: b["datum"])
    return out
