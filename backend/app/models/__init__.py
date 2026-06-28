"""Modelle importieren, damit Base.metadata sie kennt (fuer create_all)."""
from app.models.anlage import Anlage, AnlagenSonderposten
from app.models.gaap import GaapValue
from app.models.mapping import MappingEntry
from app.models.odoo_connection import OdooConnection
from app.models.saldo_snapshot import SaldoSnapshot
from app.models.stammdaten import StammdatenWert
from app.models.uebermittlung import Uebermittlung
from app.models.user import Role, User
from app.models.wirtschaftsjahr import Wirtschaftsjahr

__all__ = [
    "User",
    "Role",
    "OdooConnection",
    "Wirtschaftsjahr",
    "MappingEntry",
    "GaapValue",
    "Uebermittlung",
    "SaldoSnapshot",
    "StammdatenWert",
    "Anlage",
    "AnlagenSonderposten",
]
