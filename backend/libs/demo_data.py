"""Deterministische Demo-Daten (kein Live-Odoo).

Gleiche Form wie OdooClient.get_balances/get_company, damit der Endpunkt-Vertrag
identisch bleibt. Werte sind pro Jahr fest geseedet (stabil ueber Aufrufe).
2026 = Rumpf-Halbjahr -> ~halbe Magnitude.
"""
from __future__ import annotations

import random

_KONTEN = [
    ("0210", "Maschinen", "Anlagevermögen"),
    ("0410", "Geschäftsausstattung", "Anlagevermögen"),
    ("0135", "Immaterielle Vermögensgegenstände", "Anlagevermögen"),
    ("1200", "Bank", "Umlaufvermögen"),
    ("1000", "Kasse", "Umlaufvermögen"),
    ("1400", "Forderungen aus Lieferungen und Leistungen", "Umlaufvermögen"),
    ("1600", "Vorräte / Waren", "Umlaufvermögen"),
    ("0800", "Gezeichnetes Kapital", "Eigenkapital"),
    ("0860", "Gewinnrücklagen", "Eigenkapital"),
    ("1600", "Verbindlichkeiten aus Lieferungen und Leistungen", "Verbindlichkeiten"),
    ("1700", "Sonstige Verbindlichkeiten", "Verbindlichkeiten"),
    ("8400", "Umsatzerlöse 19% USt", "Erlöse"),
    ("8300", "Umsatzerlöse 7% USt", "Erlöse"),
    ("3400", "Wareneinkauf", "Materialaufwand"),
    ("4100", "Löhne und Gehälter", "Personalaufwand"),
    ("4120", "Gesetzliche Sozialaufwendungen", "Personalaufwand"),
    ("4210", "Miete", "Sonstiger Aufwand"),
    ("4530", "Kfz-Kosten", "Sonstiger Aufwand"),
    ("4910", "Bürobedarf", "Sonstiger Aufwand"),
    ("4360", "Versicherungen", "Sonstiger Aufwand"),
]


def _year_of(wj_bezeichnung: str) -> int:
    digits = "".join(c for c in wj_bezeichnung if c.isdigit())
    return int(digits) if digits else 2024


def demo_balances(wj_bezeichnung: str, partial: bool = False) -> list[dict]:
    """Stabile Demo-Salden fuer ein WJ. partial -> ~halbe Werte (Rumpf-WJ)."""
    year = _year_of(wj_bezeichnung)
    rng = random.Random(year)  # deterministisch pro Jahr
    faktor = 0.5 if partial else 1.0
    out: list[dict] = []
    for i, (code, name, art) in enumerate(_KONTEN):
        basis = rng.uniform(8000, 220000)
        # leichte Jahressteigerung, damit sich Jahre unterscheiden
        wachstum = 1 + (year - 2023) * 0.04
        saldo = round(basis * wachstum * faktor, 2)
        if art in ("Verbindlichkeiten", "Eigenkapital", "Erlöse"):
            saldo = -saldo  # Haben-Salden
        out.append(
            {
                "code": code,
                "name": f"{name}",
                "account_type": art,
                "saldo": saldo,
                "soll_haben": "S" if saldo >= 0 else "H",
                "buchungen": rng.randint(3, 480) // (2 if partial else 1) + 1,
                "id": f"k-{i}",
            }
        )
    return out


def demo_company() -> dict:
    return {
        "name": "Muster Verkehrs GmbH",
        "strasse": "Bahnhofstraße 1",
        "plz_ort": "80331 München",
        "ust_idnr": "DE123456789",
        "hrb": "HRB 98765",
    }
