// Zentrale API-Anbindung (fetch, ohne Zusatz-Abhaengigkeit).
// Basis-URL aus VITE_API_BASE (.env); Default = Backend auf Netzwerk-IP.

const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://10.0.100.3:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

function authHeader(): Record<string, string> {
  const token = localStorage.getItem('ebilanz_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...authHeader(), ...(init.headers ?? {}) },
      ...init,
    })
  } catch {
    throw new ApiError(0, 'Backend nicht erreichbar.')
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = (body as { detail?: string }).detail ?? msg
    } catch {
      /* keine JSON-Fehlermeldung */
    }
    throw new ApiError(res.status, msg)
  }
  return (await res.json()) as T
}

// --- DTOs (Backend-Antworten) ----------------------------------------------
export interface WjDto {
  id: number
  bezeichnung: string
  von: string // ISO-Datum
  bis: string
  taxonomie_version: string
  taxonomie_label: string
  status: string
}
export interface HealthDto {
  status: string
  env: string
  db: boolean
  odoo_configured: boolean
  odoo_db?: string | null
}
export interface TaxonomienDto {
  versionen: string[]
  arten: string[]
  default: string
}
export interface FinanzamtDto {
  bufa: string | null
  name: string
}
export interface FinanzaemterDto {
  bundeslaender: string[]
  nach_bundesland: Record<string, FinanzamtDto[]>
}
export interface OdooConfigDto {
  url: string
  db: string
  username: string
  company_id: number
  protocol: string
  configured: boolean
  api_key_set: boolean
}
export interface OdooConfigInput {
  url: string
  db: string
  username: string
  api_key: string
  company_id: number
  protocol: string
}
export interface OdooTestDto {
  ok: boolean
  uid: number
  server_version: string | null
  latency_ms: number
  models: Record<string, boolean>
}
export interface CompanyDto {
  source: string
  name: string
  rechtsform: string
  strasse: string
  plz_ort: string
  bundesland: string
  ust_idnr: string
  hrb: string
  telefon?: string
  email?: string
  website?: string
}
export interface BalanceRowDto {
  id?: string
  code: string
  name: string
  account_type: string
  saldo: number
  soll_haben: 'S' | 'H'
  buchungen: number
  diff?: 'neu' | 'geaendert' | 'entfernt' | 'unveraendert'
}
export interface BalancesDto {
  source: string
  wj: string
  rows: BalanceRowDto[]
}
export interface TokenDto {
  access_token: string
  token_type: string
  role: string
  email: string
}

// --- Mapping / GAAP / Kontennachweise / Validierung / Übermittlung ----------
export interface TaxNodeDto {
  id: string
  label: string
  feldtyp?: string
  children?: TaxNodeDto[]
}
export interface MappingAccountDto {
  account_key: string
  code: string
  name: string
  saldo: number
  account_type: string
  status: string
  position_id: string | null
  position_label: string | null
  suggestion: { position_id: string; label: string; confidence: number } | null
}
export interface MappingDto {
  positions: TaxNodeDto[]
  accounts: MappingAccountDto[]
}
export interface AssignmentDto {
  account_key: string
  position_id: string | null
  position_label: string | null
  status: string
}
export interface GaapNodeDto {
  id: string
  label: string
  feldtyp?: string
  importwert?: number
  wertFinal?: number | null
  nil?: boolean
  children?: GaapNodeDto[]
}
export interface GaapDto {
  bestandteil: string
  nodes: GaapNodeDto[]
}
export interface GaapEntryDto {
  position_id: string
  wert_final: number | null
  nil: boolean
}
export interface KontennachweisGruppeDto {
  id: string
  label: string
  status: 'vollständig' | 'fehlt'
  konten: { code: string; name: string; saldo: number }[]
}
export interface BuchungDto {
  datum: string
  beleg: string
  text: string
  betrag: number
}
export interface PruefmeldungDto {
  id: string
  schwere: 'Fehler' | 'Hinweis'
  code: string
  position: string
  meldung: string
  route: string
}
export interface ValidierungDto {
  ampel: 'success' | 'warning' | 'danger'
  fehler: number
  hinweis: number
  geprueft_am: string
  meldungen: PruefmeldungDto[]
}
export interface UebermittlungDto {
  id: number
  wj: string
  datum: string
  modus: 'Test' | 'Echt'
  status: string
  transfer_ticket: string
  benutzer: string
  rueckmeldung: string
}

export const API_BASE_URL = API_BASE

export const api = {
  health: () => request<HealthDto>('/api/health'),
  wirtschaftsjahre: () => request<WjDto[]>('/api/wirtschaftsjahre'),
  taxonomien: () => request<TaxonomienDto>('/api/taxonomien'),
  finanzaemter: () => request<FinanzaemterDto>('/api/finanzaemter'),
  company: () => request<CompanyDto>('/api/odoo/company'),
  odooConfig: () => request<OdooConfigDto>('/api/odoo/config'),
  saveOdooConfig: (cfg: OdooConfigInput) =>
    request<OdooConfigDto>('/api/odoo/config', { method: 'PUT', body: JSON.stringify(cfg) }),
  testOdoo: (cfg: OdooConfigInput) =>
    request<OdooTestDto>('/api/odoo/test', { method: 'POST', body: JSON.stringify(cfg) }),
  balances: (wj: number) => request<BalancesDto>(`/api/odoo/balances?wj=${wj}`),
  balancesUebernehmen: (wj: number) =>
    request<{ uebernommen: number }>(`/api/odoo/balances/${wj}/uebernehmen`, { method: 'POST' }),
  login: (email: string, password: string) =>
    request<TokenDto>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  mapping: (wj: number) => request<MappingDto>(`/api/mapping/${wj}`),
  saveMapping: (wj: number, assignments: AssignmentDto[]) =>
    request<{ updated: number }>(`/api/mapping/${wj}`, {
      method: 'PUT',
      body: JSON.stringify({ assignments }),
    }),
  gaap: (wj: number, bestandteil: string) => request<GaapDto>(`/api/gaap/${wj}/${bestandteil}`),
  saveGaap: (wj: number, bestandteil: string, werte: GaapEntryDto[]) =>
    request<{ gespeichert: number }>(`/api/gaap/${wj}/${bestandteil}`, {
      method: 'PUT',
      body: JSON.stringify({ werte }),
    }),
  kontennachweise: (wj: number) =>
    request<KontennachweisGruppeDto[]>(`/api/kontennachweise/${wj}`),
  buchungen: (wj: number, konto: string) =>
    request<BuchungDto[]>(`/api/kontennachweise/${wj}/buchungen?konto=${encodeURIComponent(konto)}`),
  validieren: (wj: number) =>
    request<ValidierungDto>(`/api/validierung/${wj}`, { method: 'POST' }),
  uebermitteln: (wj: number, modus: 'test' | 'echt') =>
    request<UebermittlungDto>(`/api/uebermittlung/${wj}`, {
      method: 'POST',
      body: JSON.stringify({ modus }),
    }),
  uebermittlungen: (wj?: number) =>
    request<UebermittlungDto[]>(`/api/uebermittlungen${wj ? `?wj_id=${wj}` : ''}`),
}
