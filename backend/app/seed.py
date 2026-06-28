"""DB-Initialisierung + idempotentes Seeding (Super-Admin, Odoo-Config, 4 WJ)."""
import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ROOT_DIR, settings
from app.database import Base, SessionLocal, engine
from app.models import (
    Anlage,
    AnlagenSonderposten,
    GaapValue,
    OdooConnection,
    Role,
    User,
    Wirtschaftsjahr,
)
from app.security import hash_password
from libs.ebilanz_demo import (
    ANLAGEN_DEMO,
    GAAP_BESTANDTEILE,
    KLASSE_LABEL,
    SONDERPOSTEN_DEMO,
    gaap_value_leaves,
)


def _ensure_data_dir() -> None:
    settings.db_file.parent.mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data" / "sqlite_backups").mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """Tabellen anlegen und seeden (idempotent)."""
    _ensure_data_dir()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_superadmin(db)
        seed_odoo_from_env(db)
        seed_wirtschaftsjahre(db)
        db.commit()
        seed_gaap_values(db)
        db.commit()
        seed_anlagen(db)
        db.commit()
    finally:
        db.close()


def seed_superadmin(db: Session) -> None:
    existing = db.scalar(select(User).where(User.email == settings.superadmin_email))
    if existing:
        return
    db.add(
        User(
            email=settings.superadmin_email,
            password_hash=hash_password(settings.superadmin_password),
            role=Role.admin,
            is_superadmin=True,
            active=True,
        )
    )


def seed_odoo_from_env(db: Session) -> None:
    row = db.scalar(select(OdooConnection).limit(1))
    if row is None:
        row = OdooConnection()
        db.add(row)
    # .env nur beim Erst-Setup uebernehmen; spaetere UI-Aenderungen nicht ueberschreiben.
    if settings.odoo_url and not row.configured:
        row.url = settings.odoo_url
        row.db = settings.odoo_db
        row.username = settings.odoo_username
        row.api_key = settings.odoo_api_key
        row.company_id = settings.odoo_company_id
        row.protocol = settings.odoo_rpc


# Vier Wirtschaftsjahre (Demo): 2023, 2024, 2025, 2026 (Rumpf bis 30.06.2026).
_WJ_SEED = [
    ("WJ 2023", datetime.date(2023, 1, 1), datetime.date(2023, 12, 31), "6.9", "Kern 6.9", "Echtfall gesendet"),
    ("WJ 2024", datetime.date(2024, 1, 1), datetime.date(2024, 12, 31), "6.9", "Kern 6.9 + JAbschlVUV", "In Bearbeitung"),
    ("WJ 2025", datetime.date(2025, 1, 1), datetime.date(2025, 12, 31), "6.10", "Kern 6.10", "Validiert OK"),
    ("WJ 2026", datetime.date(2026, 1, 1), datetime.date(2026, 6, 30), "6.10", "Kern 6.10", "Entwurf"),
]


def seed_wirtschaftsjahre(db: Session) -> None:
    for bezeichnung, von, bis, tver, tlabel, status in _WJ_SEED:
        if db.scalar(select(Wirtschaftsjahr).where(Wirtschaftsjahr.bezeichnung == bezeichnung)):
            continue
        db.add(
            Wirtschaftsjahr(
                bezeichnung=bezeichnung,
                von=von,
                bis=bis,
                taxonomie_version=tver,
                taxonomie_label=tlabel,
                status=status,
            )
        )


# WJ mit bereits erfassten Werten (Importwert uebernommen). WJ 2026 (Entwurf)
# bleibt leer -> demonstriert Mussfeld-/Validierungs-Guards.
_GAAP_SEED_WJ = {"WJ 2023", "WJ 2024", "WJ 2025"}


def seed_gaap_values(db: Session) -> None:
    """Erfasste GAAP-Werte (wert_final = Importwert) fuer bearbeitete WJ seeden.

    Idempotent je WJ: ein WJ wird nur befuellt, wenn es noch keine eigene
    GaapValue-Zeile hat (robust gegen Altbestaende anderer WJ).
    """
    wjs = db.scalars(
        select(Wirtschaftsjahr).where(Wirtschaftsjahr.bezeichnung.in_(_GAAP_SEED_WJ))
    ).all()
    for wj in wjs:
        if db.scalar(select(GaapValue).where(GaapValue.wj_id == wj.id).limit(1)):
            continue  # WJ bereits befuellt
        for bestandteil in GAAP_BESTANDTEILE:
            for leaf in gaap_value_leaves(bestandteil):
                db.add(
                    GaapValue(
                        wj_id=wj.id,
                        bestandteil=bestandteil,
                        position_id=leaf["id"],
                        wert_final=leaf["importwert"],
                        nil=False,
                    )
                )


def seed_anlagen(db: Session) -> None:
    """Anlagenbuchhaltung (Asset-Register + Sonderposten) je WJ seeden.

    Fuer alle WJ (der Anlagenspiegel speist sich daraus). Idempotent je WJ:
    ein WJ wird nur befuellt, wenn es noch keine Anlage hat.
    """
    for wj in db.scalars(select(Wirtschaftsjahr)).all():
        if db.scalar(select(Anlage).where(Anlage.wj_id == wj.id).limit(1)):
            continue  # WJ bereits befuellt
        erste_je_klasse: dict[str, int] = {}
        for a in ANLAGEN_DEMO:
            row = Anlage(
                wj_id=wj.id,
                klasse_id=a["klasse_id"],
                klasse_label=KLASSE_LABEL[a["klasse_id"]],
                bezeichnung=a["bezeichnung"],
                ahk=a["ahk"],
                kum_abschreibung=a["kum_abschreibung"],
                anschaffungsjahr=a.get("jahr"),
                nutzungsdauer_jahre=a.get("nd"),
            )
            db.add(row)
            db.flush()  # row.id fuer Sonderposten-Zuordnung
            erste_je_klasse.setdefault(a["klasse_id"], row.id)
        for s in SONDERPOSTEN_DEMO:
            db.add(
                AnlagenSonderposten(
                    wj_id=wj.id,
                    anlage_id=erste_je_klasse.get(s["klasse_id"]),
                    bezeichnung=s["bezeichnung"],
                    geber=s.get("geber", ""),
                    stand_anfang=s["stand_anfang"],
                    zugang=s["zugang"],
                    aufloesung=s["aufloesung"],
                )
            )
