# PRD – UI · E-Bilanz App

**Produkt:** E-Bilanz Übermittlung · `ebilanz.simplify-erp.de`
**Modell:** Single-Instance je Odoo-Kunde · Datenquelle Odoo (XML-/JSON-RPC) · Persistenz SQLite · Übermittlung via ERiC-Sidecar
**Sprache UI:** Deutsch · **Stack:** Vue 3 + Vite · **Fonts:** Source Sans Pro / Fira Code (selbst gehostet) · **Branding:** simplify-erp.de
**Arbeitsobjekt:** *E-Bilanz-Projekt* = 1 Wirtschaftsjahr (WJ)

---

## 1. Design-System

### 1.1 Tokens
Quelle: simplify-erp.de Design-System (`simplify-flywheel/website/src/index.css`).
Zwei-Ton-Palette: Blau = primär, Rot = danger. Kein Grün — `success` rendert blau.

```json
{
  "color": {
    "primary": "#0077B5",
    "primary-700": "#005A8C",
    "primary-600": "#006399",
    "secondary": "#EA5562",
    "secondary-700": "#D94450",
    "bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "border": "#DEE3E8",
    "text": "#22262B",
    "muted": "#6C757D",
    "success": "#0077B5",
    "warning": "#E6A100",
    "danger": "#EA5562",
    "info": "#0077B5"
  },
  "radius": { "card": 12, "control": 10, "pill": 999 },
  "shadow": {
    "card": "0 1px 3px 0 rgba(0,0,0,.1), 0 1px 2px -1px rgba(0,0,0,.1)",
    "pop": "0 8px 24px rgba(16,24,40,.12)"
  },
  "font": { "base": "'Source Sans Pro', system-ui, sans-serif", "mono": "'Fira Code', monospace" },
  "space": [4, 8, 12, 16, 24, 32, 48]
}
```
Hinweise: `control` 10px = simplify `--radius` (0.625rem); `card` 12px (lg+2). `shadow.card` = simplify `--shadow`. Primär-Blau `#0077B5` = HSL 201 100% 35%; danger-Rot `#EA5562`.

### 1.2 Komponenten-Inventar
- **Card** · KPI-Card · Status-Card · Aktions-Card (groß)
- **DataGrid** (virtuell, Inline-Edit, Spalten-Filter, Gruppierung, Sticky-Header)
- **Stepper** (horizontal, Workflow)
- **Big-Prompt** (Hero-CTA, Empty-State, große Schaltflächen ≥ 56px)
- **Badge / Pill** (Status, Feldtyp, Taxonomie-Version)
- **Banner** (Info / Warnung / Fehler, persistent)
- **Drawer** (rechts, Detail/Edit) · **Modal** (Bestätigung)
- **Toast** (Aktionsfeedback)
- **Split-Pane** (Mapping: links Konten / rechts Positionen)
- **Inline-Validation-Chip** (Mussfeld, Summenfehler)

### 1.3 Statusfarben (global, einheitlich)
Zwei-Ton-Palette: `success`/`info`/`primary` lösen alle zu Blau `#0077B5` auf. Blaue Status werden über die **Füllung** der Pill unterschieden: solid = `success` (Validiert OK, Echtfall gesendet); soft/outline = `info` (In Bearbeitung, Testfall gesendet); `primary-700` (dunkler) = Geprüft. `warning` = Amber, `danger` = Rot.

```json
{
  "Entwurf": "muted",
  "In Bearbeitung": "info",
  "Geprüft": "primary",
  "Validiert OK": "success",
  "Validierung Fehler": "danger",
  "Testfall gesendet": "info",
  "Echtfall gesendet": "success",
  "Abgelehnt": "danger",
  "Berichtigung": "warning"
}
```

---

## 2. App-Shell

### 2.1 Topbar (sticky, 64px)
- Logo (links) → Dashboard
- **WJ-Selector** (Dropdown: aktives E-Bilanz-Projekt / Wirtschaftsjahr)
- **Taxonomie-Badge** (z. B. `Kern 6.9 + JAbschlVUV`) — Klick → Taxonomie-Info
- **ERiC-Status-Pill** (grün „ERiC 41.x aktiv" / rot „Update nötig")
- **Odoo-Verbindung-Indikator** (grün/rot Punkt)
- **Hilfe** (?) · **Benutzer-Menü** (Avatar → Profil, Rolle, Logout)

### 2.2 Linkes Hauptmenü (Sidebar, einklappbar, 260px)
```json
[
  { "icon": "grid", "label": "Übersicht", "route": "/dashboard" },
  { "icon": "building", "label": "Stammdaten (GCD)", "route": "/stammdaten" },
  { "icon": "upload", "label": "Saldenimport", "route": "/import" },
  { "icon": "git-merge", "label": "Konten-Mapping", "route": "/mapping", "badge": "offen: {n}" },
  { "icon": "table", "label": "E-Bilanz Erfassung", "route": "/gaap",
    "children": [
      { "label": "Bilanz", "route": "/gaap/bilanz" },
      { "label": "Gewinn- und Verlustrechnung", "route": "/gaap/guv" },
      { "label": "Ergebnisverwendung", "route": "/gaap/ergebnisverwendung" },
      { "label": "Steuerliche Gewinnermittlung", "route": "/gaap/steuerlich" },
      { "label": "Überleitungsrechnung", "route": "/gaap/ueberleitung" },
      { "label": "Anlagenspiegel", "route": "/gaap/anlagenspiegel" }
    ]
  },
  { "icon": "list", "label": "Kontennachweise", "route": "/kontennachweise" },
  { "icon": "check-circle", "label": "Validierung", "route": "/validierung", "badge": "{fehler}" },
  { "icon": "send", "label": "Übermittlung", "route": "/uebermittlung" },
  { "icon": "history", "label": "Protokoll & Historie", "route": "/protokoll" }
]
```
- Fortschritts-Indikator je Eintrag (Punkt: leer / teil / voll)
- Unten fixiert: **„Jetzt validieren"** (sekundär) · **„Übermitteln"** (primär, groß)

### 2.3 Admin-Menü (separater Bereich, Zahnrad → `/admin`)
```json
[
  { "icon": "sliders", "label": "Unternehmen & WJ", "route": "/admin/unternehmen" },
  { "icon": "users", "label": "Benutzer & Rollen", "route": "/admin/benutzer" },
  { "icon": "cpu", "label": "ERiC-Verwaltung", "route": "/admin/eric" },
  { "icon": "shield", "label": "Zertifikate", "route": "/admin/zertifikate" },
  { "icon": "hash", "label": "Hersteller-ID", "route": "/admin/hersteller-id" },
  { "icon": "layers", "label": "Taxonomie-Verwaltung", "route": "/admin/taxonomie" },
  { "icon": "link", "label": "Odoo-Verbindung", "route": "/admin/odoo" },
  { "icon": "file-text", "label": "Audit-Log", "route": "/admin/audit" },
  { "icon": "settings", "label": "Einstellungen", "route": "/admin/einstellungen" }
]
```

### 2.4 Rollen → Sichtbarkeit
```json
{
  "Sachbearbeiter": ["dashboard","stammdaten","import","mapping","gaap","kontennachweise","validierung"],
  "Bilanzbuchhalter": ["+ueberleitung","+anlagenspiegel","+protokoll"],
  "Steuerberater/Freigeber": ["+uebermittlung","+freigabe"],
  "Admin": ["alles","admin/*"]
}
```

---

## 3. Views (Haupt)

### 3.1 Übersicht / Dashboard `/dashboard`
**Zweck:** Status des aktiven WJ, nächster Schritt.
- **Big-Prompt** oben: aktueller WJ + nächste empfohlene Aktion (z. B. „3 Mussfelder offen → Mapping abschließen"), große CTA.
- **Workflow-Stepper** (1 Stammdaten → 2 Import → 3 Mapping → 4 Erfassung → 5 Validierung → 6 Übermittlung).
- **KPI-Cards (4er-Grid):**
```json
[
  { "titel": "Mapping-Quote", "wert": "92%", "sub": "412/448 Konten" },
  { "titel": "Offene Mussfelder", "wert": "3", "status": "warning" },
  { "titel": "Validierungsfehler", "wert": "0", "status": "success" },
  { "titel": "Letzte Übermittlung", "wert": "—", "sub": "noch nicht gesendet" }
]
```
- **Status-Card Datenquelle:** Odoo-Verbindung, letzter Saldenstand-Abruf (Timestamp), ERiC-Version, Taxonomie-Version.
- **Aktivitäts-Feed** (letzte Änderungen, Wer/Was/Wann).

### 3.2 Stammdaten (GCD) `/stammdaten`
**Layout:** 2-spaltig, Cards je Themenblock. Quelle-Badge je Feld (`Odoo` / `manuell`).
**Formular (JSON):**
```json
{
  "unternehmen": [
    { "key": "name", "label": "Firmenname", "typ": "text", "quelle": "res.company.name", "readonly": true },
    { "key": "rechtsform", "label": "Rechtsform", "typ": "select", "quelle": "manuell", "mussfeld": true,
      "optionen": ["GmbH","AG","GmbH & Co. KG","OHG","e.K.","..."] },
    { "key": "strasse", "label": "Straße", "typ": "text", "quelle": "res.company.street" },
    { "key": "plz_ort", "label": "PLZ / Ort", "typ": "text", "quelle": "res.company.zip+city" },
    { "key": "bundesland", "label": "Bundesland", "typ": "select", "quelle": "manuell", "mussfeld": true }
  ],
  "steuer": [
    { "key": "steuernummer", "label": "Steuernummer (ELSTER)", "typ": "tax-id", "quelle": "manuell", "mussfeld": true,
      "hinweis": "≠ USt-IdNr; Landesschema" },
    { "key": "ust_idnr", "label": "USt-IdNr", "typ": "text", "quelle": "res.company.vat" },
    { "key": "finanzamt", "label": "Finanzamt", "typ": "select", "quelle": "manuell", "mussfeld": true },
    { "key": "hrb", "label": "Handelsregister (HRB)", "typ": "text", "quelle": "res.company.company_registry" }
  ],
  "bericht": [
    { "key": "wj_von", "label": "WJ von", "typ": "date", "quelle": "account.fiscal.year", "mussfeld": true },
    { "key": "wj_bis", "label": "WJ bis", "typ": "date", "quelle": "account.fiscal.year", "mussfeld": true },
    { "key": "taxonomie_version", "label": "Taxonomie-Version", "typ": "select", "quelle": "manuell", "mussfeld": true,
      "optionen": ["6.9","6.10"] },
    { "key": "branchentaxonomie", "label": "Ergänzungstaxonomie", "typ": "multiselect", "quelle": "manuell",
      "optionen": ["Keine","Verkehrsunternehmen (JAbschlVUV)","Wohnungswirtschaft","KHBV","..."] },
    { "key": "bilanzierungsstandard", "label": "Bilanzierungsstandard", "typ": "select", "mussfeld": true,
      "optionen": ["Deutsches Steuerrecht","Deutsches Handelsrecht","Einheitsbilanz"] },
    { "key": "groessenklasse", "label": "Größenklasse (§ 267 HGB)", "typ": "select",
      "optionen": ["Kleinst","Klein","Mittel","Groß"] }
  ]
}
```
- **CTAs:** `Aus Odoo aktualisieren` (sekundär) · `Speichern` (primär) · Banner bei fehlenden Mussfeldern.

### 3.3 Saldenimport `/import`
**Zweck:** Salden live aus Odoo ziehen (kein CSV-Pflicht), optional Datei-Upload.
- **Big-Prompt:** „Salden aus Odoo abrufen" (große CTA) + Periodenangabe (WJ vorbelegt).
- **Filter-Card:** WJ-Zeitraum · `parent_state=posted` (fix) · Konten-Status (aktiv/deprecated).
- **Vorschau-DataGrid (read-only):**
```json
{
  "columns": [
    { "field": "code", "header": "Konto", "width": 110, "sort": true },
    { "field": "name", "header": "Bezeichnung", "flex": 1 },
    { "field": "account_type", "header": "Kontoart", "width": 160 },
    { "field": "saldo", "header": "Saldo (EUR)", "align": "right", "format": "de-EUR" },
    { "field": "soll_haben", "header": "S/H", "width": 60 },
    { "field": "buchungen", "header": "#Buchungen", "align": "right", "width": 110 }
  ],
  "features": ["virtual-scroll","spalten-filter","summe-footer","diff-zu-letztem-import"]
}
```
- **CTAs:** `Import übernehmen` (primär) · `Als Datei importieren` (sekundär, CSV/DATEV/XBRL Fallback) · `Verwerfen`.
- **States:** Diff-Badge je Konto (neu / geändert / entfernt) vs. letztem Abruf.

### 3.4 Konten-Mapping `/mapping`
**Layout:** Split-Pane (links Odoo-Konten · rechts Taxonomie-Positionen) + Vorschlag-Engine.
- **Linkes Grid – Konten:**
```json
{
  "columns": [
    { "field": "code", "header": "Konto", "width": 100 },
    { "field": "name", "header": "Bezeichnung", "flex": 1 },
    { "field": "saldo", "header": "Saldo", "align": "right", "format": "de-EUR" },
    { "field": "mapping_status", "header": "Status", "render": "pill" }
  ],
  "row_status": ["nicht zugeordnet","zugeordnet","Auffangposition","Konflikt"]
}
```
- **Rechtes Panel – Position-Auswahl:** Taxonomie-Baum (suchbar), Feldtyp-Badge je Position:
```json
{ "feldtypen": ["Mussfeld","Summenmussfeld","Kontennachweis erwünscht","rechnerisch notwendig","Auffangposition"] }
```
- **Regeln (Inline-Validation):**
  - Direkte Zuordnung auf **Summenmussfeld** → blockiert → Hinweis „Unterposition oder Auffangposition wählen".
  - Auto-Vorschlag aus `account_type` + `group_id` + SKR-Code → Chip „Vorschlag" mit Konfidenz.
- **Bulk-Aktionen:** Mehrfachauswahl → Position zuweisen · Vorschläge übernehmen · zurücksetzen.
- **Mapping-Sets:** speichern/laden je Kontenrahmen (SKR03/04), versioniert je Taxonomie-Version.
- **CTAs:** `Vorschläge übernehmen` · `Mapping speichern` · `Offene anzeigen` (Filter) · **Big-Prompt** bei unzugeordneten Mussfeldern.

### 3.5 E-Bilanz Erfassung (GAAP) `/gaap/*`
**Gemeinsames Muster je Berichtsbestandteil:**
- Taxonomie-getriebene Erfassungsmaske, hierarchisch (Baum-Grid), aus Mapping vorbefüllt, **editierbar**.
```json
{
  "grid": {
    "columns": [
      { "field": "position", "header": "Taxonomie-Position", "tree": true, "flex": 1 },
      { "field": "feldtyp", "header": "Typ", "render": "pill", "width": 130 },
      { "field": "wert_import", "header": "Importwert", "align": "right", "readonly": true, "format": "de-EUR" },
      { "field": "wert_final", "header": "Erfasster Wert", "align": "right", "editable": true, "format": "de-EUR" },
      { "field": "differenz", "header": "Δ", "align": "right", "render": "diff" },
      { "field": "fussnote", "header": "Fußnote", "render": "icon-toggle" }
    ],
    "features": ["inline-edit","summen-rollup","abweichungs-highlight","mussfeld-marker","NIL-toggle"]
  }
}
```
- **NIL/Leerwert-Handling:** Mussfeld ohne Sachverhalt → Toggle „kein Sachverhalt (NIL)".
- **Per-Bestandteil:**
  - **Bilanz / GuV:** abgeleitet, editierbar.
  - **Ergebnisverwendung:** nur Kapitalgesellschaft (Öffis: GmbH → aktiv).
  - **Steuerliche Gewinnermittlung / Betriebsvermögensvergleich.**
  - **Überleitungsrechnung:** HGB→Steuer; nur bei Bilanzierungsstandard „Handelsrecht"; je Position Anpassungszeile + Begründung.
  - **Anlagenspiegel:** Quelle `account.asset` (Enterprise) ODER manuelle Erfassung (Community-Gap-Banner).
- **CTAs je Maske:** `Speichern` · `Aus Mapping neu berechnen` · `Als geprüft markieren` (Vier-Augen).

### 3.6 Kontennachweise `/kontennachweise`
**Zweck:** Unverdichtete Kontennachweise je werthaltiger Position (JStG 2024).
- **Gruppen-DataGrid:** gruppiert nach Taxonomie-Position → darunter Konten (code, name, saldo).
- Drill-down Drawer → Einzelbuchungen (`account.move.line`, optional).
- **Status-Chip:** „vollständig" / „fehlt" je Position.
- **CTAs:** `Nachweise generieren` · `Lücken anzeigen` · `Export (Prüfung)`.

### 3.7 Validierung `/validierung`
**Zweck:** ERiC-Prüfungen (Plausibilität, Mussfeld, Summen) vor Versand.
- **Big-Prompt:** großer Button **„Jetzt mit ERiC prüfen"** + letzter Prüfzeitpunkt.
- **Ergebnis-Card:** Ampel (OK / Warnungen / Fehler) + Zähler.
- **Fehler-DataGrid:**
```json
{
  "columns": [
    { "field": "schwere", "header": "Schwere", "render": "pill", "values": ["Fehler","Hinweis"] },
    { "field": "code", "header": "ERiC-Code", "width": 130 },
    { "field": "position", "header": "Position/Feld", "flex": 1 },
    { "field": "meldung", "header": "Meldung", "flex": 2 },
    { "field": "aktion", "header": "", "render": "button:Zum Feld" }
  ]
}
```
- **Click-to-field:** Zeile → springt in zugehörige GAAP-Maske, Feld fokussiert.
- **CTAs:** `Erneut prüfen` · `Bericht exportieren` · (bei OK) `Weiter zur Übermittlung` (primär groß).

### 3.8 Übermittlung `/uebermittlung`
**Layout:** Stepper-Wizard.
```json
{
  "schritte": [
    { "id": 1, "titel": "Vorschau", "inhalt": "gerenderte Bilanz/GuV + XBRL-Vorschau" },
    { "id": 2, "titel": "Zertifikat", "inhalt": "Zertifikat wählen + PIN" },
    { "id": 3, "titel": "Modus", "inhalt": "Testfall (Testmerker) | Echtfall (Toggle, groß)" },
    { "id": 4, "titel": "Bestätigung", "inhalt": "Zusammenfassung + Freigabe-Hinweis" }
  ]
}
```
- **Big-Prompt CTAs:**
  - `Als Testfall senden` (sekundär, immer erlaubt)
  - **`Echtfall übermitteln`** (primär, groß, rot-Akzent, nur nach Validierung OK + Freigabe)
- **Guard:** Echtfall gesperrt, bis Status „Validiert OK" + Freigeber-Rolle bestätigt.
- **Nach Versand:** Lock des Datensatzes, Toast + Weiterleitung zu Protokoll.

### 3.9 Protokoll & Historie `/protokoll`
- **DataGrid Übermittlungen:**
```json
{
  "columns": [
    { "field": "datum", "header": "Datum/Zeit", "format": "de-datetime" },
    { "field": "wj", "header": "WJ", "width": 90 },
    { "field": "modus", "header": "Modus", "render": "pill", "values": ["Test","Echt"] },
    { "field": "status", "header": "Status", "render": "pill" },
    { "field": "transfer_ticket", "header": "Transfer-Ticket", "mono": true },
    { "field": "pdf", "header": "ERiC-PDF", "render": "download" },
    { "field": "benutzer", "header": "Durch", "width": 140 }
  ]
}
```
- **Detail-Drawer:** Rückmeldung (Roh + lesbar), gesendetes XBRL, Validierungsstand zum Zeitpunkt.
- **Banner-Reminder:** „Bundesanzeiger-Offenlegung separat erforderlich".
- **CTAs:** `Berichtigung erstellen` (kopiert Datensatz → neues Projekt, Status „Berichtigung") · `XBRL herunterladen` · `PDF herunterladen`.

---

## 4. Admin-Views

### 4.1 Unternehmen & WJ `/admin/unternehmen`
- Card Unternehmensdaten (Sync-Status Odoo).
- **E-Bilanz-Projekte-Grid:** WJ · Taxonomie-Version · Status · Aktionen (öffnen / archivieren / duplizieren).
- CTA: `Neues WJ-Projekt anlegen` (großer Prompt) → Wizard (WJ-Zeitraum, Taxonomie-Version, Branche, Mapping-Set übernehmen).

### 4.2 Benutzer & Rollen `/admin/benutzer`
- Grid: Name · E-Mail · Rolle · letzter Login · Status.
- Rollen-Editor (Sachbearbeiter / Bilanzbuchhalter / Steuerberater-Freigeber / Admin).
- Vier-Augen-Pflicht-Toggle (Trennung Erfassung ↔ Freigabe).

### 4.3 ERiC-Verwaltung `/admin/eric`
- **Status-Card:** installierte ERiC-Version · Release-Datum · Sidecar-Health (grün/rot) · letzte Selbstprüfung.
- **Update-Banner:** „Neues ERiC-Release verfügbar" → CTA `Update prüfen`.
- Release-Historie-Grid · Verbindungstest-Button.

### 4.4 Zertifikate `/admin/zertifikate`
- Grid: Zertifikat · Inhaber · Gültig bis (Ablauf-Warnung-Pill) · Status.
- CTAs: `Zertifikat hochladen` (verschlüsselt) · `Ablauf testen`.
- Sicherheits-Banner (Speicherung im Vault, PIN nie persistiert).

### 4.5 Hersteller-ID `/admin/hersteller-id`
- Card: Hersteller-ID + Status · Hinweis-Text (Pflicht für Übermittlung).
- CTA: `ID hinterlegen` / `ändern`.

### 4.6 Taxonomie-Verwaltung `/admin/taxonomie`
- Grid installierter Taxonomie-Pakete: Version · gültig ab WJ · Status (aktiv / Vorschau / archiviert).
- CTAs: `Paket importieren` (ZIP von esteuer.de) · `Auf Updates prüfen` · `Änderungsnachweis ansehen`.
- Watcher-Banner: „Version 6.x veröffentlicht (BMF-Schreiben …)".

### 4.7 Odoo-Verbindung `/admin/odoo`
- Form: URL · DB · Auth (User/API-Key) · `company_id`.
```json
{
  "felder": [
    { "key": "url", "label": "Odoo-URL", "typ": "url" },
    { "key": "db", "label": "Datenbank", "typ": "text" },
    { "key": "api_key", "label": "API-Key", "typ": "password" },
    { "key": "company_id", "label": "Unternehmen (company_id)", "typ": "number" },
    { "key": "rpc", "label": "Protokoll", "typ": "select", "optionen": ["JSON-RPC","XML-RPC"] }
  ]
}
```
- CTAs: `Verbindung testen` · `Felder-Mapping prüfen` (zeigt fehlende native Felder → custom).
- Status-Card: letzter erfolgreicher Abruf, Latenz, Modell-Verfügbarkeit (`account.asset` ja/nein → Community-Hinweis).

### 4.8 Audit-Log `/admin/audit`
- DataGrid (immutable): Zeit · Benutzer · Objekt · Aktion · alt→neu.
- Filter: Benutzer / Zeitraum / Objekttyp. Export.

### 4.9 Einstellungen `/admin/einstellungen`
- Zahlenformat (de-DE), Rundung, Fußnoten-Vorlagen, Benachrichtigungen (E-Mail bei Release/Ablauf), Backup SQLite (Export/Import).

---

## 5. Globale CTA-Matrix

Rot (`#EA5562`) ist ausschließlich für `danger` und den `Echtfall übermitteln`-CTA reserviert — so bleibt die destruktive Aktion trotz Zwei-Ton-Palette visuell eindeutig. Alle übrigen primären CTAs sind blau.

```json
[
  { "cta": "Aus Odoo aktualisieren", "typ": "sekundär", "kontext": "Stammdaten, Import" },
  { "cta": "Import übernehmen", "typ": "primär", "kontext": "Saldenimport" },
  { "cta": "Vorschläge übernehmen", "typ": "sekundär", "kontext": "Mapping" },
  { "cta": "Mapping speichern", "typ": "primär", "kontext": "Mapping" },
  { "cta": "Jetzt mit ERiC prüfen", "typ": "primär-groß", "kontext": "Validierung" },
  { "cta": "Als Testfall senden", "typ": "sekundär", "kontext": "Übermittlung" },
  { "cta": "Echtfall übermitteln", "typ": "primär-groß-danger", "kontext": "Übermittlung", "guard": "validiert_ok && freigeber" },
  { "cta": "Berichtigung erstellen", "typ": "warning", "kontext": "Protokoll" },
  { "cta": "Neues WJ-Projekt anlegen", "typ": "primär-groß", "kontext": "Admin/Unternehmen" }
]
```

---

## 6. Status- & Empty-States (Big-Prompts)

```json
[
  { "view": "Dashboard", "empty": "Noch kein WJ angelegt", "cta": "WJ-Projekt anlegen" },
  { "view": "Import", "empty": "Noch keine Salden", "cta": "Salden aus Odoo abrufen" },
  { "view": "Mapping", "empty": "Keine Konten geladen", "cta": "Zum Saldenimport" },
  { "view": "Validierung", "empty": "Noch nicht geprüft", "cta": "Jetzt mit ERiC prüfen" },
  { "view": "Übermittlung", "blocked": "Validierung offen/fehlerhaft", "cta": "Zur Validierung" },
  { "view": "Anlagenspiegel", "warning": "account.asset nicht verfügbar (Community)", "cta": "Manuell erfassen" }
]
```

---

## 7. Workflow-Guards (Zustandslogik)

```json
{
  "kann_validieren": "stammdaten_vollständig && mapping_mussfelder_ok",
  "kann_testfall": "xbrl_generierbar",
  "kann_echtfall": "validierung_ok && zertifikat_gewählt && hersteller_id && freigabe_erteilt",
  "sperre_nach_versand": true,
  "korrektur_nur_als": "Berichtigung (neuer Datensatz)"
}
```

---

## 8. Responsives Verhalten
- Sidebar → einklappbar < 1280px, Off-canvas < 960px.
- DataGrids: horizontal scrollbar + Sticky erste Spalte.
- Erfassungsmasken: Baum-Grid behält Einrückung; Werte-Spalten priorisiert.
- Big-Prompts skalieren (Hero auf Desktop, kompakt mobil).
