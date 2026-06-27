"""Odoo-Endpunkte: Konfiguration, Verbindungstest, Unternehmen, Salden.

Ohne konfigurierte Odoo-Verbindung liefern company/balances deterministische
Demo-Daten (source="demo"); andernfalls Live-Odoo (source="odoo").
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db, get_odoo_client
from app.models import OdooConnection, SaldoSnapshot, User, Wirtschaftsjahr
from app.schemas.odoo import OdooConfigIn, OdooConfigOut
from libs.demo_data import demo_balances, demo_company
from libs.odoo_client import OdooClient, OdooError

router = APIRouter(prefix="/api/odoo", tags=["odoo"])

# Rechtsform aus dem Firmennamen ableiten (laengste Endung zuerst).
_RECHTSFORMEN = ["GmbH & Co. KG", "gGmbH", "GmbH", "AG", "OHG", "KG", "e.K.", "SE", "UG"]


def _rechtsform_aus_name(name: str) -> str:
    n = name.strip()
    for rf in _RECHTSFORMEN:
        if n.endswith(rf):
            return rf
    return ""


def _merge_company(c: dict) -> dict:
    """Live-Odoo-Werte mit Installations-Fallback (.env, z. B. Impressum) zusammenfuehren.

    Fuer jedes Feld: Odoo-Wert, sonst COMPANY_*-Fallback.
    """
    name = c.get("name") or ""

    def pick(key: str, fallback: str) -> str:
        return (c.get(key) or "") or fallback

    return {
        "name": name,
        "rechtsform": settings.company_rechtsform or _rechtsform_aus_name(name),
        "strasse": pick("strasse", settings.company_strasse),
        "plz_ort": pick("plz_ort", settings.company_plz_ort),
        "bundesland": pick("bundesland", settings.company_bundesland),
        "ust_idnr": pick("ust_idnr", settings.company_ust_idnr),
        "hrb": pick("hrb", settings.company_hrb),
        "telefon": pick("telefon", settings.company_telefon),
        "email": pick("email", settings.company_email),
        "website": pick("website", settings.company_website),
    }


def _row(db: Session) -> OdooConnection:
    row = db.scalar(select(OdooConnection).limit(1))
    if row is None:
        row = OdooConnection()
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/config", response_model=OdooConfigOut)
def get_config(db: Session = Depends(get_db)):
    row = _row(db)
    return OdooConfigOut(
        url=row.url, db=row.db, username=row.username, company_id=row.company_id,
        protocol=row.protocol, configured=row.configured, api_key_set=bool(row.api_key),
    )


@router.put("/config", response_model=OdooConfigOut)
def put_config(body: OdooConfigIn, db: Session = Depends(get_db)):
    # Hinweis: Rollen-Gating folgt mit dem Auth-Slice (todo §E).
    row = _row(db)
    row.url, row.db, row.username = body.url, body.db, body.username
    row.company_id, row.protocol = body.company_id, body.protocol
    if body.api_key:  # leeren Wert nicht ueberschreiben
        row.api_key = body.api_key
    db.commit()
    db.refresh(row)
    return OdooConfigOut(
        url=row.url, db=row.db, username=row.username, company_id=row.company_id,
        protocol=row.protocol, configured=row.configured, api_key_set=bool(row.api_key),
    )


@router.post("/test")
def test_connection(body: OdooConfigIn | None = None, db: Session = Depends(get_db)):
    """Verbindung testen — wahlweise die übergebenen Formularwerte oder die gespeicherte Config.

    Leerer API-Key im Formular -> gespeicherter Key wird verwendet (Secret wird nie ausgegeben).
    """
    row = _row(db)
    if body and body.url and body.db:
        client = OdooClient(
            url=body.url, db=body.db, username=body.username,
            api_key=body.api_key or row.api_key,
            company_id=body.company_id, protocol=body.protocol,
        )
    elif row.configured:
        client = OdooClient(
            url=row.url, db=row.db, username=row.username, api_key=row.api_key,
            company_id=row.company_id, protocol=row.protocol,
        )
    else:
        raise HTTPException(400, "Odoo nicht konfiguriert.")
    try:
        return client.test_connection()
    except OdooError as exc:
        raise HTTPException(exc.status, exc.message) from exc


@router.get("/company")
def company(client: OdooClient | None = Depends(get_odoo_client)):
    if client is None:
        return {"source": "demo", **_merge_company(demo_company())}
    try:
        return {"source": "odoo", **_merge_company(client.get_company())}
    except OdooError as exc:
        raise HTTPException(exc.status, exc.message) from exc


def _aktuelle_salden(projekt: Wirtschaftsjahr, client: OdooClient | None) -> tuple[str, list[dict]]:
    """Aktuelle Salden (live Odoo oder Demo) fuer ein WJ holen."""
    if client is None:
        partial = (projekt.bis.month, projekt.bis.day) != (12, 31)
        return "demo", demo_balances(projekt.bezeichnung, partial=partial)
    return "odoo", client.get_balances(projekt.von, projekt.bis)


def _mit_diff(rows: list[dict], wj_id: int, db: Session) -> list[dict]:
    """Diff der aktuellen Salden gegen den zuletzt übernommenen Import (PRD §3.3)."""
    snap = {
        s.code: s
        for s in db.scalars(
            select(SaldoSnapshot).where(SaldoSnapshot.wj_id == wj_id)
        ).all()
    }
    out: list[dict] = []
    aktuelle_codes = set()
    for r in rows:
        code = r["code"]
        aktuelle_codes.add(code)
        s = snap.get(code)
        if not snap:
            diff = "neu"  # noch kein Import -> alles neu
        elif s is None:
            diff = "neu"
        elif round(s.saldo, 2) != round(float(r["saldo"]), 2):
            diff = "geaendert"
        else:
            diff = "unveraendert"
        out.append({**r, "diff": diff})
    # Im Snapshot, aber nicht mehr in den aktuellen Salden -> entfernt
    for code, s in snap.items():
        if code not in aktuelle_codes:
            out.append({
                "id": "snap-" + code,
                "code": code,
                "name": s.name,
                "account_type": s.account_type,
                "saldo": s.saldo,
                "soll_haben": s.soll_haben,
                "buchungen": s.buchungen,
                "diff": "entfernt",
            })
    return out


@router.get("/balances")
def balances(
    wj: int = Query(..., description="Wirtschaftsjahr-ID"),
    db: Session = Depends(get_db),
    client: OdooClient | None = Depends(get_odoo_client),
):
    projekt = db.get(Wirtschaftsjahr, wj)
    if projekt is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    try:
        source, rows = _aktuelle_salden(projekt, client)
    except OdooError as exc:
        raise HTTPException(exc.status, exc.message) from exc
    return {"source": source, "wj": projekt.bezeichnung, "rows": _mit_diff(rows, wj, db)}


@router.post("/balances/{wj}/uebernehmen")
def balances_uebernehmen(
    wj: int,
    db: Session = Depends(get_db),
    client: OdooClient | None = Depends(get_odoo_client),
):
    """Aktuelle Salden als neuen Import-Baseline-Snapshot uebernehmen."""
    projekt = db.get(Wirtschaftsjahr, wj)
    if projekt is None:
        raise HTTPException(404, "Wirtschaftsjahr nicht gefunden.")
    try:
        _source, rows = _aktuelle_salden(projekt, client)
    except OdooError as exc:
        raise HTTPException(exc.status, exc.message) from exc
    # Alten Snapshot ersetzen.
    db.query(SaldoSnapshot).filter(SaldoSnapshot.wj_id == wj).delete()
    for r in rows:
        db.add(SaldoSnapshot(
            wj_id=wj,
            code=r["code"],
            name=r.get("name", ""),
            account_type=r.get("account_type", ""),
            saldo=float(r.get("saldo", 0.0)),
            soll_haben=r.get("soll_haben", "S"),
            buchungen=int(r.get("buchungen", 0)),
        ))
    db.commit()
    return {"uebernommen": len(rows)}
