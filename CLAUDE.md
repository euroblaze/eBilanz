# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project State

Greenfield. The repo currently holds **only** `ebilanz-ui-prd.md` — a detailed UI Product Requirements Document. No code, build tooling, tests, or git history exist yet. There are no build/lint/test commands to run; they must be created as the app is scaffolded.

When scaffolding, follow the global conventions in `~/.claude/CLAUDE.md` (folder layout: `backend/`, `web-UI/`, `scripts/`, `tests/`, `specs/`, `docs/`; Python backend; Vue 3 + Vite frontend; German locale/Euros; snake_case filenames; element IDs on every `<div>`).

## What This App Is

**E-Bilanz Übermittlung** (`ebilanz.simplify-erp.de`) — a German e-balance-sheet (tax) filing app. It pulls accounting data from **Odoo** (XML-/JSON-RPC), maps it to the official German **XBRL taxonomy**, validates it, and transmits it to the tax authority (Finanzamt) via an **ERiC sidecar**.

Deployment model: **single instance per Odoo customer**. Persistence is **SQLite**. UI is **German, Vue 3 + Vite**.

## Core Domain Model

The central work object is an **E-Bilanz-Projekt = one Wirtschaftsjahr (WJ / fiscal year)**. Nearly all state is scoped to the active WJ (selected via the topbar WJ-Selector). Understanding this scoping is essential — dashboard, import, mapping, GAAP entry, validation, and submission all operate on the currently selected WJ project.

Key external dependencies that shape the architecture:
- **Odoo** — data source via RPC. Reads `res.company`, `account.fiscal.year`, account balances (`parent_state=posted`), `account.move.line`, and (Enterprise only) `account.asset`. Community edition lacks `account.asset` → Anlagenspiegel must be entered manually (gap banner).
- **ERiC sidecar** — separate service performing tax-office validation and the actual transmission. App must track its version/health and surface update needs.
- **German XBRL Taxonomy** — versioned (e.g. Kern 6.9/6.10) plus branch extensions (e.g. JAbschlVUV). Taxonomy packages are imported as ZIPs from esteuer.de.

## The Workflow Pipeline (drives the whole UI)

The app is structured as a strict 6-step pipeline; each step gates the next via **Workflow-Guards** (see PRD §7):

1. **Stammdaten (GCD)** — company/tax master data; mix of Odoo-sourced and manual fields.
2. **Saldenimport** — pull account balances live from Odoo (CSV/DATEV/XBRL upload is fallback only).
3. **Konten-Mapping** — map Odoo accounts → taxonomy positions (split-pane). Has a suggestion engine (`account_type` + `group_id` + SKR code → confidence chip). Mapping-Sets are saved/versioned per Kontenrahmen (SKR03/04) and taxonomy version. **Rule:** direct mapping onto a Summenmussfeld is blocked.
4. **E-Bilanz Erfassung (GAAP)** — taxonomy-driven tree-grid entry masks, prefilled from mapping but editable: Bilanz, GuV, Ergebnisverwendung, Steuerliche Gewinnermittlung, Überleitungsrechnung, Anlagenspiegel. Supports NIL (kein Sachverhalt) toggles for Mussfelder.
5. **Validierung** — run ERiC checks (Mussfeld, sums, plausibility). Errors link click-to-field back into the GAAP masks.
6. **Übermittlung** — wizard: Vorschau → Zertifikat+PIN → Modus (Testfall/Echtfall) → Bestätigung. After send: record is locked; corrections only via a new **Berichtigung** record.

Critical guards (do not bypass): `kann_echtfall = validierung_ok && zertifikat_gewählt && hersteller_id && freigabe_erteilt`. Echtfall (real submission) requires a Freigeber (approver) role and a passed validation. Vier-Augen-Prinzip (separation of Erfassung ↔ Freigabe) is enforceable.

## Roles & Visibility

Sachbearbeiter → Bilanzbuchhalter → Steuerberater/Freigeber → Admin, additive visibility (PRD §2.4). Only Freigeber can perform Echtfall submission. Admin area (`/admin/*`) covers Unternehmen&WJ, Benutzer&Rollen, ERiC-Verwaltung, Zertifikate, Hersteller-ID, Taxonomie-Verwaltung, Odoo-Verbindung, Audit-Log, Einstellungen.

## Security-Sensitive Areas (from PRD)

- Zertifikate stored encrypted in a vault; **PIN is never persisted**.
- Hersteller-ID is mandatory for any transmission.
- Audit-Log is immutable (Zeit · Benutzer · Objekt · Aktion · alt→neu).

## UI Design System

Defined in PRD §1. Tokens: primary `#1D9E75`, full color/radius/shadow/space scale, fonts Inter/JetBrains Mono. Fixed status→color map (§1.3) and a component inventory (DataGrid with virtual scroll/inline-edit, Stepper, Big-Prompt heroes, Split-Pane, Drawer/Modal/Toast, validation chips). Number format is de-DE, currency EUR. Reuse these tokens/components rather than introducing new ones.

## Reference

`ebilanz-ui-prd.md` is the authoritative spec for all views, fields, grids, CTAs, empty-states, and guards. Consult it (with section numbers) before implementing any view; per global convention, formal features go in `specs/` and reference it.
