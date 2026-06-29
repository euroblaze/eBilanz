# eBilanz Übermittlung

E-Bilanz-Filing-App: zieht Buchungsdaten aus **Odoo**, mappt sie auf die deutsche
**XBRL-Taxonomie**, validiert und übermittelt via **ERiC-Sidecar** ans Finanzamt.
Backend = FastAPI (Python), Frontend = Vue 3 + Vite, Persistenz = SQLite.
Eine Instanz pro Odoo-Kunde. UI deutsch, Währung EUR.

## Voraussetzungen

- Python 3 (Backend-venv unter `backend/.venv`)
- Node.js + npm (Frontend)
- `.env` im Repo-Root (siehe Schlüssel unten)

## Erstinstallation

```bash
# Backend-venv + Abhängigkeiten
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..

# Frontend-Abhängigkeiten
cd web-UI && npm install && cd ..
```

`.env` im Repo-Root anlegen (12-Factor, keine Secrets im Code). Wichtige Schlüssel
(Defaults siehe `backend/app/config.py`):

```
HOST=0.0.0.0
PORT=8000
SQLITE_PATH=./data/ebilanz.sqlite
CORS_ORIGINS=http://10.0.99.1:5173,http://localhost:5173
SUPERADMIN_EMAIL=...
SUPERADMIN_PASSWORD=...
ODOO_URL=...        # leer -> Demo-Daten
ODOO_DB=...
ODOO_USERNAME=...
ODOO_API_KEY=...
```

Die SQLite-DB wird beim ersten Backend-Start automatisch angelegt und geseedet
(Superadmin aus `.env`, Demo-Wirtschaftsjahre). Optional manuell:

```bash
backend/.venv/bin/python scripts/sqlite_db.py init
```

## Starten / Stoppen

`scripts/run-ebilanz.sh` startet Backend und Frontend **direkt** als
Hintergrundprozesse (keine pm2-Abhängigkeit). PIDs liegen in `run/`,
Logs in `logs/` (beide gitignored).

```bash
scripts/run-ebilanz.sh start              # Backend + Frontend
scripts/run-ebilanz.sh status             # Status + belegte Ports
scripts/run-ebilanz.sh stop               # beide stoppen
scripts/run-ebilanz.sh restart --frontend # nur Frontend neu starten
scripts/run-ebilanz.sh logs --backend -f  # Backend-Log live verfolgen
```

| Aktion    | Wirkung |
|-----------|---------|
| `start`   | Komponente(n) im Hintergrund starten (bereits laufende werden übersprungen) |
| `stop`    | SIGTERM, nach Karenzzeit SIGKILL; reapt die ganze Prozessgruppe (npm + vite) |
| `restart` | stop + start |
| `status`  | je Komponente: running/stopped/stale + ob der Port lauscht |
| `logs`    | Log einer Komponente anzeigen (Standard: letzte 40 Zeilen) |

**Ziele:** `--frontend` · `--backend` · `--all` (Standard für start/stop/restart/status = beide)
**Optionen:** `--lines <n>` · `-f/--follow` (logs) · `-d/--dry-run` · `-h/--help`

## Adressen

- Backend (FastAPI): `http://10.0.99.1:8000` — Health: `GET /api/health`
- Frontend (Vite): `http://10.0.99.1:5173`

Host/Port des Backends kommen aus `.env` (`HOST`, `PORT`; Default `0.0.0.0:8000`).
Frontend-Port `5173` ist in `web-UI/vite.config.ts` gesetzt; das Backend-Ziel des
Frontends steuert `web-UI/.env` (`VITE_API_BASE`).

## Verzeichnisse

```
backend/     FastAPI-Backend (app/, libs/, .venv/)
web-UI/      Vue-3-/Vite-Frontend
scripts/     run-ebilanz.sh (Start/Stop), sqlite_db.py (DB-Wartung)
data/        SQLite-DB + Backups (data/sqlite_backups/)
```

## Referenz

`ebilanz-ui-prd.md` ist die maßgebliche UI-/Feature-Spezifikation.
`CLAUDE.md` enthält Projekt- und Architekturhinweise.
