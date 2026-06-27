"""Wiederverwendbarer Odoo-RPC-Client (XML-RPC + JSON-RPC).

Wird vom Backend (routers) und von scripts/ genutzt. Alle Netzwerk-/Auth-Fehler
werden zu OdooError gekapselt (deutsche Meldung) — nie ein roher Stacktrace.
"""
from __future__ import annotations

import time
import xmlrpc.client
from datetime import date

import requests


class OdooError(Exception):
    """Gekapselter Odoo-Fehler mit nutzerfreundlicher Meldung."""

    def __init__(self, message: str, *, status: int = 502):
        super().__init__(message)
        self.message = message
        self.status = status


class OdooClient:
    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        api_key: str,
        company_id: int = 1,
        protocol: str = "jsonrpc",
        timeout: int = 15,
    ):
        if not url or not db:
            raise OdooError("Odoo nicht konfiguriert.", status=400)
        # RPC liegt am Server-Root (/jsonrpc, /xmlrpc/2). "/odoo" ist nur der Web-Client-Pfad
        # (Odoo 17+). Trailing-Slash und trailing "/odoo" entfernen, damit beide Formen gehen.
        base = url.rstrip("/")
        if base.endswith("/odoo"):
            base = base[: -len("/odoo")]
        self.url = base.rstrip("/")
        self.db = db
        self.username = username
        self.api_key = api_key
        self.company_id = company_id
        self.protocol = protocol
        self.timeout = timeout
        self._uid: int | None = None

    # ---- Low-level -----------------------------------------------------------
    def _xmlrpc(self, endpoint: str):
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/{endpoint}", allow_none=True)

    def _jsonrpc(self, service: str, method: str, args: list):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
        try:
            resp = requests.post(f"{self.url}/jsonrpc", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            raise OdooError(f"Odoo nicht erreichbar: {exc}") from exc
        if "error" in data:
            msg = data["error"].get("data", {}).get("message") or data["error"].get("message")
            raise OdooError(f"Odoo-Fehler: {msg}", status=400)
        return data.get("result")

    def version(self) -> dict:
        try:
            if self.protocol == "xmlrpc":
                return self._xmlrpc("common").version()
            return self._jsonrpc("common", "version", [])
        except OdooError:
            raise
        except Exception as exc:  # noqa: BLE001 — alles kapseln
            raise OdooError(f"Odoo nicht erreichbar: {exc}") from exc

    def authenticate(self) -> int:
        if self._uid is not None:
            return self._uid
        try:
            if self.protocol == "xmlrpc":
                uid = self._xmlrpc("common").authenticate(
                    self.db, self.username, self.api_key, {}
                )
            else:
                uid = self._jsonrpc(
                    "common", "authenticate", [self.db, self.username, self.api_key, {}]
                )
        except OdooError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise OdooError(f"Odoo-Authentifizierung fehlgeschlagen: {exc}") from exc
        if not uid:
            raise OdooError("Odoo-Anmeldung abgelehnt (Benutzer/API-Key prüfen).", status=400)
        self._uid = int(uid)
        return self._uid

    def execute_kw(self, model: str, method: str, args: list, kwargs: dict | None = None):
        uid = self.authenticate()
        params = [self.db, uid, self.api_key, model, method, args, kwargs or {}]
        try:
            if self.protocol == "xmlrpc":
                return self._xmlrpc("object").execute_kw(*params)
            return self._jsonrpc("object", "execute_kw", params)
        except OdooError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise OdooError(f"Odoo-Abfrage fehlgeschlagen ({model}.{method}): {exc}") from exc

    # ---- High-level ----------------------------------------------------------
    def check_model(self, model: str) -> bool:
        try:
            self.execute_kw("ir.model", "search_count", [[["model", "=", model]]])
            return True
        except OdooError:
            return False

    def test_connection(self) -> dict:
        started = time.monotonic()
        ver = self.version()
        uid = self.authenticate()
        latency = round((time.monotonic() - started) * 1000)
        return {
            "ok": True,
            "uid": uid,
            "server_version": ver.get("server_version") if isinstance(ver, dict) else None,
            "latency_ms": latency,
            "models": {
                "account.asset": self.check_model("account.asset"),
                "account.fiscal.year": self.check_model("account.fiscal.year"),
            },
        }

    def get_company(self, company_id: int | None = None) -> dict:
        cid = company_id or self.company_id
        fields = [
            "name", "street", "zip", "city", "vat", "company_registry",
            "country_id", "state_id", "phone", "email", "website",
        ]
        rows = self.execute_kw("res.company", "read", [[cid]], {"fields": fields})
        if not rows:
            # Fallback: erstes Unternehmen, falls company_id nicht passt.
            rows = self.execute_kw(
                "res.company", "search_read", [[]], {"fields": fields, "limit": 1}
            )
        if not rows:
            raise OdooError("Kein Unternehmen (res.company) gefunden.", status=404)
        c = rows[0]
        state = c.get("state_id")
        return {
            "name": c.get("name") or "",
            "strasse": c.get("street") or "",
            "plz_ort": f"{c.get('zip') or ''} {c.get('city') or ''}".strip(),
            "ust_idnr": c.get("vat") or "",
            "hrb": c.get("company_registry") or "",
            "bundesland": (state[1] if isinstance(state, list) else "") or "",
            "telefon": c.get("phone") or "",
            "email": c.get("email") or "",
            "website": c.get("website") or "",
        }

    def get_balances(
        self, date_from: date, date_to: date, company_id: int | None = None
    ) -> list[dict]:
        cid = company_id or self.company_id
        domain = [
            ["parent_state", "=", "posted"],
            ["company_id", "=", cid],
            ["date", ">=", date_from.isoformat()],
            ["date", "<=", date_to.isoformat()],
        ]
        groups = self.execute_kw(
            "account.move.line",
            "read_group",
            [domain, ["balance:sum"], ["account_id"]],
            {"lazy": False},
        )
        # Kontodetails (code/name/account_type) je Konto nachladen.
        acc_ids = [g["account_id"][0] for g in groups if isinstance(g.get("account_id"), list)]
        acc_map: dict[int, dict] = {}
        if acc_ids:
            for a in self.execute_kw(
                "account.account", "read", [acc_ids],
                {"fields": ["code", "name", "account_type"]},
            ):
                acc_map[a["id"]] = a
        out: list[dict] = []
        for g in groups:
            acc = g.get("account_id")
            if not isinstance(acc, list):
                continue
            info = acc_map.get(acc[0], {})
            saldo = round(float(g.get("balance") or 0.0), 2)
            out.append(
                {
                    "code": info.get("code") or acc[1].split(" ")[0],
                    "name": info.get("name") or acc[1],
                    "account_type": _ACCOUNT_TYPE_DE.get(
                        info.get("account_type", ""), info.get("account_type") or ""
                    ),
                    "saldo": saldo,
                    "soll_haben": "S" if saldo >= 0 else "H",
                    "buchungen": int(g.get("__count") or 0),
                }
            )
        return out


# Odoo account_type (Selection) -> deutsche Kontoart-Bezeichnung (Anzeige/Filter).
_ACCOUNT_TYPE_DE = {
    "asset_receivable": "Forderungen",
    "asset_cash": "Liquide Mittel",
    "asset_current": "Umlaufvermögen",
    "asset_non_current": "Anlagevermögen",
    "asset_prepayments": "Aktive Rechnungsabgrenzung",
    "asset_fixed": "Sachanlagen",
    "liability_payable": "Verbindlichkeiten",
    "liability_credit_card": "Kreditkarte",
    "liability_current": "kurzfristige Verbindlichkeiten",
    "liability_non_current": "langfristige Verbindlichkeiten",
    "equity": "Eigenkapital",
    "equity_unaffected": "Ergebnisvortrag",
    "income": "Erlöse",
    "income_other": "sonstige Erträge",
    "expense": "Aufwand",
    "expense_depreciation": "Abschreibungen",
    "expense_direct_cost": "Materialaufwand",
    "off_balance": "außerbilanziell",
}
