# eBilanz — Implementierungs-Checkliste

Stand: 2026-06-27. Referenz: `ebilanz-ui-prd.md` (PRD). Legende: `- [x]` erledigt · `- [ ]` offen.

Kurzstatus: Frontend-Gerüst + alle 9 Hauptansichten (§3) auf Mock-Daten stehen; Backend-Gerüst
(FastAPI + SQLite + Odoo-Client + Demo-Daten + Login) steht. Es fehlen: Frontend↔API-Anbindung,
9 Admin-Ansichten (§4), die E-Bilanz-Kern-Engine (Taxonomie/XBRL/ERiC), Rollen-/Guard-Durchsetzung,
Docker, Tests. Aktionen, die nur Du erledigen kannst, stehen in **Abschnitt H**.

---

## A. Bereits erledigt

### Frontend-Fundament
- [x] Vue 3 + Vite + TypeScript + Pinia + Vue Router (`web-UI/`)
- [x] Tailwind mit simplify-erp.de Tokens (Zwei-Ton Blau/Rot), `src/styles/tokens.css`
- [x] Selbst gehostete Fonts (Source Sans 3 / Fira Code, GDPR, kein Google-CDN)
- [x] App-Shell: Topbar (WJ-Selector, Status-Pills) + einklappbare Sidebar (§2.1/§2.2)
- [x] Wiederverwendbare Komponenten: button, card, badge_pill, banner, big_prompt,
      workflow_stepper, data_grid (TanStack), drawer, split_pane, taxonomy_tree, gaap_grid
- [x] de-DE Formatierungs-Helfer (EUR, Datum) `src/libs/format.ts`
- [x] PRD §1 auf simplify-erp.de Branding umgestellt (Tokens/Fonts)

### Hauptansichten (§3) — auf Mock-Daten
- [x] Dashboard `/dashboard` (§3.1)
- [x] Stammdaten `/stammdaten` (§3.2)
- [x] Saldenimport `/import` mit DataGrid (§3.3)
- [x] Konten-Mapping `/mapping` (Split-Pane, Vorschläge, Summenmussfeld-Sperre) (§3.4)
- [x] E-Bilanz Erfassung `/gaap/*` (6 Bestandteile, Tree-Grid, NIL, Rollup) (§3.5)
- [x] Kontennachweise `/kontennachweise` (Gruppen + Drill-down Drawer) (§3.6)
- [x] Validierung `/validierung` (Ampel, Fehler-Grid, Click-to-field) (§3.7)
- [x] Übermittlung `/uebermittlung` (Stepper-Wizard, Echtfall-Guard) (§3.8)
- [x] Protokoll `/protokoll` (Grid + Detail-Drawer) (§3.9)

### Backend-Gerüst
- [x] FastAPI-App + CORS auf Netzwerk-IP, Startup-Seed (`backend/app/main.py`)
- [x] 12-Factor Config aus `.env` (`config.py`)
- [x] SQLite + SQLAlchemy Modelle: user, odoo_connection, wirtschaftsjahr (normalisiert, Date-Objekte)
- [x] Super-Admin-Seed aus `.env` + 4 Wirtschaftsjahre (2023–2026, 2026 Rumpf bis 30.06.)
- [x] JWT-Login `/api/auth/login` (bcrypt)
- [x] Odoo-Client (XML-RPC + JSON-RPC, typisierte Fehler) `backend/libs/odoo_client.py`
- [x] Deterministische Demo-Daten (2026 Halbjahr) `backend/libs/demo_data.py`
- [x] Endpunkte: health, odoo config/test/company/balances, wirtschaftsjahre
- [x] `scripts/sqlite_db.py` (init/backup/restore, Backups in `data/sqlite_backups/`)

---

## B. Frontend — offen

### API-Anbindung (Mocks ersetzen)
- [ ] API-Service-Layer (axios) + `VITE_API_BASE` (.env) + Auth-Token-Interceptor
- [ ] Pinia Auth-Store + Login-Screen + Route-Guards (Token, Rolle)
- [ ] WJ-Selector → `GET /api/wirtschaftsjahre` (statt MOCK_PROJEKTE in `wj_store.ts`)
- [ ] Stammdaten → `GET/PUT` company + manuelle Felder
- [ ] Saldenimport → `GET /api/odoo/balances?wj=` (inkl. Diff-zu-letztem-Abruf)
- [ ] Mapping → Konten/Positionen/Mapping-Sets/Vorschläge über API
- [ ] GAAP → Werte laden/speichern (NIL, Rollup) über API
- [ ] Kontennachweise → Positionen + Einzelbuchungen (Drill-down) über API
- [ ] Validierung → ERiC-Ergebnisse über API
- [ ] Übermittlung → Versand (Test/Echt) + Vorschau/XBRL über API
- [ ] Protokoll → Übermittlungs-Historie über API
- [ ] Lade-/Fehler-/Empty-States je Ansicht (echte Netzwerkzustände)

### Admin-Ansichten (§4) — noch keine vorhanden
- [ ] Unternehmen & WJ `/admin/unternehmen` (WJ-Projekte-Grid, Neues-WJ-Wizard) (§4.1)
- [ ] Benutzer & Rollen `/admin/benutzer` (Rollen-Editor, Vier-Augen-Toggle) (§4.2)
- [ ] ERiC-Verwaltung `/admin/eric` (Version, Sidecar-Health, Update-Banner) (§4.3)
- [ ] Zertifikate `/admin/zertifikate` (Upload, Ablauf-Warnung, Vault-Hinweis) (§4.4)
- [ ] Hersteller-ID `/admin/hersteller-id` (§4.5)
- [ ] Taxonomie-Verwaltung `/admin/taxonomie` (Paket-Import, Update-Check) (§4.6)
- [ ] Odoo-Verbindung `/admin/odoo` (Form + Verbindungstest + Feld-Mapping-Check) (§4.7)
- [ ] Audit-Log `/admin/audit` (immutable Grid, Filter, Export) (§4.8)
- [ ] Einstellungen `/admin/einstellungen` (Zahlenformat, Fußnoten, Backup) (§4.9)
- [ ] Admin-Bereich Routing + Zahnrad-Einstieg (§2.3)

### Querschnitt
- [ ] Rollenbasierte Menü-Sichtbarkeit im Frontend (§2.4)
- [ ] Globale Toast- und Modal-(Bestätigung)-Komponente (PRD §1.2)
- [ ] i18n-Framework (vue-i18n), auch wenn vorerst nur Deutsch
- [ ] Responsive-Durchlauf (§8: Sidebar Off-canvas <960px, Sticky-Spalten, Baum-Grid)
- [ ] Audit „jedes Element/jeder div hat eindeutige Id" (globale Regel)
- [ ] Barrierefreiheit (Fokus, ARIA, Tastaturbedienung der Grids/Trees)

---

## C. Backend — offen (API + Persistenz)

### Persistenz + Endpunkte je Ansicht
- [ ] Stammdaten: manuelle Felder speichern/laden (Mussfeld-Validierung)
- [ ] Mapping-Sets: speichern/laden je Kontenrahmen (SKR03/04), versioniert je Taxonomie
- [ ] Mapping-Vorschlag-Engine (account_type + group_id + SKR → Konfidenz)
- [ ] GAAP-Werte: Erfassung, NIL, Summen-Rollup, „als geprüft" (Vier-Augen)
- [ ] Kontennachweise: Positionen + `account.move.line` Drill-down, Vollständigkeit
- [ ] Validierungsergebnisse persistieren (Lauf-Historie)
- [ ] Übermittlungen/Protokoll: Datensatz, Transfer-Ticket, Rückmeldung, PDF
- [ ] Berichtigung: Datensatz kopieren → neues Projekt (Status „Berichtigung")

### Odoo-Erweiterungen
- [ ] Wirtschaftsjahr/Perioden aus Odoo (`account.fiscal.year`)
- [ ] Einzelbuchungen `account.move.line` (Drill-down)
- [ ] Anlagenspiegel: `account.asset` (Enterprise) + Community-Gap-Handling
- [ ] Feld-Mapping-Check (fehlende native Felder → custom) (§4.7)

### Auth / Rollen / Guards
- [ ] Rollen-Sichtbarkeit (§2.4) + Workflow-Guards (§7) serverseitig durchsetzen
- [ ] Vier-Augen-Prinzip (Trennung Erfassung ↔ Freigabe)
- [ ] Benutzer-CRUD, Passwort-Reset, Token-Refresh
- [ ] Audit-Log (immutable) für alle Mutationen (§4.8)

---

## D. E-Bilanz Kern-Engine (der fachlich schwierige Teil)

### Taxonomie
- [x] Offizielle Taxonomie-Optionen in Stammdaten angeboten: `Kerntaxonomie` (Simplify-ERP) +
      `Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV)` (Öffis); geteilte Konstanten + API
      `GET /api/taxonomien` + `DEFAULT_TAXONOMIE_ART` je Installation
- [ ] Import/Parsing der esteuer.de-Taxonomie-Pakete (ZIP) inkl. vollständiger amtlicher
      Ergänzungs-/Spezialtaxonomie-Liste
- [ ] Versionierung (6.9/6.10 + Branchen, z. B. JAbschlVUV) + gültig-ab-WJ
- [ ] Feldtypen (Muss/Summenmuss/Kontennachweis/rechnerisch/Auffang) modellieren
- [ ] Positions-Baum als Quelle für Mapping + GAAP (statt Mock-Baum)

### XBRL-Erzeugung
- [ ] XBRL-Generator (GCD-Stammdaten + GAAP-Module) aus erfassten Daten
- [ ] NIL-Behandlung, Summen-/Rechenregeln, Kontennachweise einbetten
- [ ] XBRL-Vorschau + Download (echt statt Mock)

### ERiC-Integration (Sidecar-Service)
- [ ] ERiC-Bibliothek in eigenem Sidecar-Service kapseln
- [ ] Plausibilitäts-/Validierungslauf (ERiC-Codes) → Validierungsansicht
- [ ] Übermittlung Testfall (Testmerker) und Echtfall
- [ ] Rückmeldung + Transfer-Ticket + ERiC-PDF verarbeiten/speichern
- [ ] ERiC-Version/Health, Hersteller-ID, Zertifikat + PIN-Fluss (PIN nie persistiert)

---

## E. Sicherheit & Compliance
- [ ] Zertifikats-Vault (verschlüsselt at rest), PIN niemals speichern (§4.4)
- [ ] Secrets-Management (keine Klartext-Keys in DB; aktuell `api_key` Klartext)
- [ ] HTTPS/TLS Ende-zu-Ende
- [ ] Man-in-the-Middle Risikoanalyse + Maßnahmen (globale Regel)
- [ ] DSGVO-Review (Datenflüsse, Aufbewahrung, AVV)
- [ ] Rate-Limiting, strikte Eingabevalidierung, Audit-Retention

---

## F. DevOps / Infrastruktur / Qualität
- [ ] Docker: getrennte Images Frontend / Backend / DB (node_modules außerhalb Image)
- [ ] docker-compose + Konfiguration je Umgebung (prod/stag/dev)
- [ ] ERiC-Sidecar Deployment (im/außerhalb Container-Netz dokumentieren)
- [ ] Tests `tests/` (pytest.ini, tests/venv, JSON-Fälle T-XXX-NNN), Backend nur via API, 90 % Coverage
- [ ] `tests/insert_mock_data.py` (bei Schemaänderungen pflegen)
- [ ] Frontend-Tests (Komponenten + e2e)
- [ ] CI-Pipeline, Logging/Monitoring, geplante Backups
- [ ] `scripts/pg_db.py` falls PostgreSQL in prod (sonst SQLite-Pfad bestätigen)

---

## G. Dokumentation
- [ ] `docs/` pflegen (Architektur, Betrieb, ERiC/Taxonomie-Handhabung)
- [ ] `specs/` nummerierte Feature-Spezifikationen + Referenzen im Code
- [ ] README aktuell halten (Setup Frontend + Backend)
- [ ] CRIE-Dokumentation bei Konsolidierungen (`docs/CRIE/`)

---

## H. AKTIONEN DURCH DICH (nur von Dir erledigbar)
- [ ] **ERiC-Bibliothek + Lizenz** und **Hersteller-ID** beschaffen (Registrierung ELSTER/BZSt)
- [ ] **ELSTER-Zertifikat(e)** (Organisation/Steuerberater, .pfx) + PIN(s) bereitstellen
- [ ] **Offizielle Taxonomie-Pakete** von esteuer.de laden (6.9/6.10 + benötigte Branchen)
- [ ] **Live-Odoo** bereitstellen: URL, DB, API-Key, company_id (+ Enterprise vs Community klären
      wegen `account.asset`/Anlagenspiegel)
- [ ] Auf dem Server `sudo apt install python3-venv python3-pip` (oder Python-Tooling bestätigen)
- [ ] **Produktions-Secrets** in `.env` setzen (SECRET_KEY, SUPERADMIN_*)
- [ ] Entscheidung **PostgreSQL vs SQLite** für Produktion
- [ ] **Hosting/Domain** (`ebilanz.simplify-erp.de`) + TLS-Zertifikate bereitstellen
- [ ] **Bundesanzeiger**-Offenlegungsprozess klären (separat zur E-Bilanz)
- [ ] Rechtliches: DSGVO/AVV, **steuerliche Freigabe** der erzeugten Ausgaben durch Berater
- [ ] **Echte Testdaten** liefern (reale WJ-Summen-/Saldenliste) für End-to-End-Validierung

---

## I. VOM KUNDEN BEREITZUSTELLEN (Dateneingaben)
- [ ] **SAP-Exporte der Stammdaten** (Unternehmens-/Steuer-Stammdaten aus SAP)
- [ ] **Busflotten-Daten (Anlagen)**: je Bus Anschaffungsdatum (purchase date) und
      angewandte Abschreibung (Methode, Nutzungsdauer, Restwert)
- [ ] **Kontenrahmen SKR04** (vollständiger Kontenplan)
