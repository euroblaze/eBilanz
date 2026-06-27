"""Konten-Mapping-Endpunkte (PRD §3.4). Persistiert Zuordnungen je WJ."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import MappingEntry, Wirtschaftsjahr
from libs.demo_data import demo_balances
from libs.ebilanz_demo import MAPPING_LEAVES, MAPPING_TAXONOMY

router = APIRouter(prefix="/api/mapping", tags=["mapping"])


def _wj(wj_id: int, db: Session) -> Wirtschaftsjahr:
    wj = db.get(Wirtschaftsjahr, wj_id)
    if wj is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    return wj


def _seed_if_empty(wj: Wirtschaftsjahr, db: Session) -> list[MappingEntry]:
    rows = list(db.scalars(select(MappingEntry).where(MappingEntry.wj_id == wj.id)).all())
    if rows:
        return rows
    partial = (wj.bis.month, wj.bis.day) != (12, 31)
    for i, b in enumerate(demo_balances(wj.bezeichnung, partial=partial)):
        leaf = MAPPING_LEAVES[i % len(MAPPING_LEAVES)]
        db.add(
            MappingEntry(
                wj_id=wj.id,
                account_key=b.get("id", f"k-{i}"),
                code=b["code"],
                name=b["name"],
                saldo=b["saldo"],
                account_type=b["account_type"],
                status="nicht zugeordnet",
                suggestion_position_id=leaf["id"],
                suggestion_label=leaf["label"],
                suggestion_confidence=60 + (i * 7) % 39,
            )
        )
    db.commit()
    return list(db.scalars(select(MappingEntry).where(MappingEntry.wj_id == wj.id)).all())


def _serialize(e: MappingEntry) -> dict:
    suggestion = None
    if e.suggestion_position_id:
        suggestion = {
            "position_id": e.suggestion_position_id,
            "label": e.suggestion_label,
            "confidence": e.suggestion_confidence,
        }
    return {
        "account_key": e.account_key,
        "code": e.code,
        "name": e.name,
        "saldo": e.saldo,
        "account_type": e.account_type,
        "status": e.status,
        "position_id": e.position_id,
        "position_label": e.position_label,
        "suggestion": suggestion,
    }


@router.get("/{wj_id}")
def get_mapping(wj_id: int, db: Session = Depends(get_db)):
    wj = _wj(wj_id, db)
    entries = _seed_if_empty(wj, db)
    return {"positions": MAPPING_TAXONOMY, "accounts": [_serialize(e) for e in entries]}


class Assignment(BaseModel):
    account_key: str
    position_id: str | None = None
    position_label: str | None = None
    status: str = "nicht zugeordnet"


class MappingUpdate(BaseModel):
    assignments: list[Assignment]


@router.put("/{wj_id}")
def put_mapping(wj_id: int, body: MappingUpdate, db: Session = Depends(get_db)):
    wj = _wj(wj_id, db)
    # Sicherstellen, dass Eintraege existieren (unabhaengig von vorherigem GET).
    _seed_if_empty(wj, db)
    by_key = {
        e.account_key: e
        for e in db.scalars(select(MappingEntry).where(MappingEntry.wj_id == wj.id)).all()
    }
    updated = 0
    for a in body.assignments:
        e = by_key.get(a.account_key)
        if not e:
            continue
        e.position_id = a.position_id
        e.position_label = a.position_label
        e.status = a.status
        updated += 1
    db.commit()
    return {"updated": updated}
