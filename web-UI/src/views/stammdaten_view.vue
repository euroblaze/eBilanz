<script setup lang="ts">
import { reactive, computed, ref, onMounted, watch } from 'vue'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import { TAXONOMIE_ARTEN, TAXONOMIE_VERSIONEN } from '@/libs/taxonomie'
import { api, ApiError, type FinanzaemterDto, type OdooTestDto } from '@/libs/api'
import { useWjStore } from '@/stores/wj_store'

const wj = useWjStore()

// Stammdaten (GCD) — PRD §3.2. Feld-getrieben aus PRD-JSON. Mock-Werte; Odoo-Wiring spaeter.
type Quelle = 'odoo' | 'manuell'
interface Feld {
  key: string
  label: string
  typ: 'text' | 'select' | 'date'
  quelle: Quelle
  mussfeld?: boolean
  hinweis?: string
  optionen?: string[]
}

const unternehmen: Feld[] = [
  { key: 'name', label: 'Firmenname', typ: 'text', quelle: 'odoo' },
  { key: 'rechtsform', label: 'Rechtsform', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: ['GmbH', 'AG', 'GmbH & Co. KG', 'OHG', 'e.K.'] },
  { key: 'strasse', label: 'Straße', typ: 'text', quelle: 'odoo' },
  { key: 'plz_ort', label: 'PLZ / Ort', typ: 'text', quelle: 'odoo' },
  { key: 'bundesland', label: 'Bundesland', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: ['Bayern', 'Berlin', 'Hamburg', 'Hessen', 'Nordrhein-Westfalen'] },
]
const steuer: Feld[] = [
  { key: 'steuernummer', label: 'Steuernummer (ELSTER)', typ: 'text', quelle: 'manuell', mussfeld: true, hinweis: '≠ USt-IdNr; Landesschema' },
  { key: 'ust_idnr', label: 'USt-IdNr', typ: 'text', quelle: 'odoo' },
  { key: 'finanzamt', label: 'Finanzamt', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: ['München', 'Berlin Mitte', 'Hamburg-Nord'] },
  { key: 'hrb', label: 'Handelsregister (HRB)', typ: 'text', quelle: 'odoo' },
]
const bericht: Feld[] = [
  { key: 'wj_von', label: 'WJ von', typ: 'date', quelle: 'odoo', mussfeld: true },
  { key: 'wj_bis', label: 'WJ bis', typ: 'date', quelle: 'odoo', mussfeld: true },
  { key: 'taxonomie_version', label: 'Taxonomie-Version', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: [...TAXONOMIE_VERSIONEN] },
  { key: 'taxonomie_art', label: 'Steuertaxonomie', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: [...TAXONOMIE_ARTEN], hinweis: 'Amtliche Taxonomie (esteuer.de): Kerntaxonomie oder Ergänzungstaxonomie der Branche.' },
  { key: 'bilanzierungsstandard', label: 'Bilanzierungsstandard', typ: 'select', quelle: 'manuell', mussfeld: true, optionen: ['Deutsches Steuerrecht', 'Deutsches Handelsrecht', 'Einheitsbilanz'] },
  { key: 'groessenklasse', label: 'Größenklasse (§ 267 HGB)', typ: 'select', quelle: 'manuell', optionen: ['Kleinst', 'Klein', 'Mittel', 'Groß'] },
]

const alleFelder = [...unternehmen, ...steuer, ...bericht]

// Mock-Werte: Odoo-Felder vorbefuellt, ein Mussfeld absichtlich leer (zeigt Banner).
const werte = reactive<Record<string, string>>({
  name: 'Muster Verkehrs GmbH',
  strasse: 'Bahnhofstraße 1',
  plz_ort: '80331 München',
  ust_idnr: 'DE123456789',
  hrb: 'HRB 98765',
  wj_von: '2024-01-01',
  wj_bis: '2024-12-31',
  rechtsform: 'GmbH',
  taxonomie_version: '6.9',
  // Demo-Unternehmen ist eine Verkehrs-GmbH -> Verkehrsunternehmen (JAbschlVUV).
  // Eine Software-GmbH (z. B. Simplify-ERP) würde hier 'Kerntaxonomie' wählen.
  taxonomie_art: 'Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV)',
  bilanzierungsstandard: 'Deutsches Steuerrecht',
  bundesland: 'Bayern',
  // finanzamt + steuernummer absichtlich leer -> offene Mussfelder
})

const offeneMussfelder = computed(() =>
  alleFelder.filter((f) => f.mussfeld && !werte[f.key]).map((f) => f.label),
)

const gruppen = [
  { id: 'unternehmen', titel: 'Unternehmen', felder: unternehmen },
  { id: 'steuer', titel: 'Steuer', felder: steuer },
  { id: 'bericht', titel: 'Bericht', felder: bericht },
]

// --- Bundesland -> Finanzamt (abhaengige Auswahl) --------------------------
// Volle amtliche Liste (alle Bundeslaender, Name + BUFA) aus dem Backend.
const fa = ref<FinanzaemterDto>({ bundeslaender: [], nach_bundesland: {} })

interface Option {
  value: string
  label: string
}

// Finanzaemter des aktuell gewaehlten Bundeslandes (Value = eindeutige BUFA-Nr).
const finanzamtOptionen = computed<Option[]>(() =>
  (fa.value.nach_bundesland[werte.bundesland] ?? []).map((f) => ({
    value: f.bufa ?? f.name,
    label: f.bufa ? f.bufa + ' — ' + f.name : f.name,
  })),
)

// Optionen je Select-Feld: Bundesland + Finanzamt dynamisch, sonst statisch.
function optionenFor(f: Feld): Option[] {
  if (f.key === 'bundesland' && fa.value.bundeslaender.length) {
    return fa.value.bundeslaender.map((s) => ({ value: s, label: s }))
  }
  if (f.key === 'finanzamt') return finanzamtOptionen.value
  return (f.optionen ?? []).map((s) => ({ value: s, label: s }))
}

// Hinweis je Feld: Finanzamt fuehrt durch die zweistufige Auswahl.
function hinweisFor(f: Feld): string | undefined {
  if (f.key === 'finanzamt') {
    if (!werte.bundesland) return 'Bitte zuerst Bundesland wählen.'
    return finanzamtOptionen.value.length + ' Finanzämter in ' + werte.bundesland + '.'
  }
  return f.hinweis
}

// Bundesland-Wechsel setzt die Finanzamt-Auswahl zurueck (sonst inkonsistent).
watch(
  () => werte.bundesland,
  () => {
    werte.finanzamt = ''
  },
)

// --- Odoo-Verbindung (anlegen / aktualisieren / testen) ---------------------
const odooForm = reactive({
  url: '', db: '', username: '', api_key: '', company_id: 1, protocol: 'jsonrpc',
})
const odooApiKeySet = ref(false)
const odooConfigured = ref(false)
const odooBusy = ref(false)
const odooMsg = ref<string | null>(null)
const odooTestErgebnis = ref<OdooTestDto | null>(null)
const odooTestFehler = ref<string | null>(null)

async function odooSpeichern() {
  odooBusy.value = true
  odooMsg.value = null
  try {
    const res = await api.saveOdooConfig({ ...odooForm })
    odooApiKeySet.value = res.api_key_set
    odooConfigured.value = res.configured
    odooForm.api_key = '' // Secret nicht im Formular halten
    odooMsg.value = 'Verbindung gespeichert.'
    wj.laden() // Topbar (Odoo / DB) aktualisieren
  } catch (e) {
    odooMsg.value = e instanceof ApiError ? e.message : 'Speichern fehlgeschlagen.'
  } finally {
    odooBusy.value = false
  }
}
async function odooTesten() {
  odooBusy.value = true
  odooTestErgebnis.value = null
  odooTestFehler.value = null
  try {
    odooTestErgebnis.value = await api.testOdoo({ ...odooForm })
  } catch (e) {
    odooTestFehler.value = e instanceof ApiError ? e.message : 'Test fehlgeschlagen.'
  } finally {
    odooBusy.value = false
  }
}

// Stammdaten aus dem Backend laden: Odoo-Unternehmensdaten + Taxonomie + Finanzaemter + Odoo-Config.
const laden = ref(false)
const fehler = ref<string | null>(null)
onMounted(async () => {
  laden.value = true
  try {
    const [company, tax, faedata, odoo] = await Promise.all([
      api.company(),
      api.taxonomien(),
      api.finanzaemter(),
      api.odooConfig(),
    ])
    werte.name = company.name
    werte.rechtsform = company.rechtsform || werte.rechtsform
    werte.strasse = company.strasse
    werte.plz_ort = company.plz_ort
    werte.bundesland = company.bundesland || werte.bundesland
    werte.ust_idnr = company.ust_idnr
    werte.hrb = company.hrb
    if (tax.default) werte.taxonomie_art = tax.default
    fa.value = faedata
    odooForm.url = odoo.url
    odooForm.db = odoo.db
    odooForm.username = odoo.username
    odooForm.company_id = odoo.company_id
    odooForm.protocol = odoo.protocol
    odooApiKeySet.value = odoo.api_key_set
    odooConfigured.value = odoo.configured
    await ladeWjStammdaten()
    fehler.value = null
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Stammdaten konnten nicht geladen werden.'
  } finally {
    laden.value = false
  }
})

function isoDate(d: Date): string {
  return new Date(d).toISOString().slice(0, 10)
}

// WJ-Zeitraum aus aktivem WJ + gespeicherte Stammdaten-Werte laden (je WJ).
async function ladeWjStammdaten() {
  const p = wj.aktivesProjekt
  if (p) {
    werte.wj_von = isoDate(p.von)
    werte.wj_bis = isoDate(p.bis)
  }
  const id = Number(wj.aktivesProjektId)
  if (!Number.isFinite(id)) return
  try {
    const stored = await api.stammdaten(id)
    for (const [k, v] of Object.entries(stored)) if (v) werte[k] = v
  } catch {
    /* noch nichts gespeichert / Backend offline */
  }
}
// Bei WJ-Wechsel neu laden.
watch(() => wj.aktivesProjektId, ladeWjStammdaten)

// Speichern: manuelle Felder je WJ persistieren (Odoo-Felder bleiben live).
const speichernMsg = ref<string | null>(null)
const speichernBusy = ref(false)
async function speichern() {
  const id = Number(wj.aktivesProjektId)
  if (!Number.isFinite(id)) {
    fehler.value = 'Kein gültiges Wirtschaftsjahr gewählt.'
    return
  }
  speichernBusy.value = true
  try {
    const payload: Record<string, string> = {}
    for (const f of alleFelder) if (f.quelle === 'manuell') payload[f.key] = werte[f.key] ?? ''
    const res = await api.saveStammdaten(id, payload)
    speichernMsg.value = `Stammdaten gespeichert (${res.gespeichert} Felder).`
    setTimeout(() => (speichernMsg.value = null), 2600)
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Speichern fehlgeschlagen.'
  } finally {
    speichernBusy.value = false
  }
}
</script>

<template>
  <div id="stammdaten" class="space-y-6">
    <!-- Fehler beim Laden der Stammdaten -->
    <Banner v-if="fehler" id="stammdaten-error" kind="error" titel="Stammdaten konnten nicht geladen werden">
      {{ fehler }} — läuft das Backend?
    </Banner>
    <Banner v-if="speichernMsg" id="stammdaten-saved" kind="info">{{ speichernMsg }}</Banner>

    <!-- Banner bei fehlenden Mussfeldern (PRD §3.2) -->
    <Banner
      v-if="offeneMussfelder.length"
      id="stammdaten-mussfeld-banner"
      kind="warning"
      titel="Offene Mussfelder"
    >
      Bitte ausfüllen: {{ offeneMussfelder.join(', ') }}.
    </Banner>

    <!-- 2-spaltiges Card-Layout -->
    <div id="stammdaten-grid" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <TheCard v-for="g in gruppen" :id="'card-' + g.id" :key="g.id" :titel="g.titel">
        <div :id="'fields-' + g.id" class="space-y-4">
          <div v-for="f in g.felder" :id="'field-' + f.key" :key="f.key">
            <label :for="'input-' + f.key" class="mb-1 flex items-center gap-2 text-xs font-medium text-foreground">
              {{ f.label }}
              <BadgePill v-if="f.mussfeld" :id="'muss-' + f.key" tone="danger" label="Muss" />
              <BadgePill :id="'quelle-' + f.key" :tone="f.quelle === 'odoo' ? 'info' : 'muted'" :label="f.quelle === 'odoo' ? 'Odoo' : 'manuell'" />
            </label>

            <select
              v-if="f.typ === 'select'"
              :id="'input-' + f.key"
              v-model="werte[f.key]"
              :disabled="f.key === 'finanzamt' && !werte.bundesland"
              class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
              :class="f.mussfeld && !werte[f.key] ? 'border-danger' : ''"
            >
              <option value="">— bitte wählen —</option>
              <option v-for="opt in optionenFor(f)" :id="'opt-' + f.key + '-' + opt.value" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <input
              v-else
              :id="'input-' + f.key"
              v-model="werte[f.key]"
              :type="f.typ === 'date' ? 'date' : 'text'"
              :readonly="f.quelle === 'odoo'"
              class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm read-only:bg-muted read-only:text-muted-foreground"
              :class="f.mussfeld && !werte[f.key] ? 'border-danger' : ''"
            />
            <p v-if="hinweisFor(f)" :id="'hint-' + f.key" class="mt-1 text-xs text-muted-foreground">{{ hinweisFor(f) }}</p>
          </div>
        </div>
      </TheCard>
    </div>

    <!-- CTAs (PRD §3.2) -->
    <div id="stammdaten-actions" class="flex flex-wrap justify-end gap-3">
      <TheButton id="stammdaten-odoo" variant="outline" size="lg">Aus Odoo aktualisieren</TheButton>
      <TheButton id="stammdaten-save" variant="primary" size="lg" :disabled="speichernBusy" @click="speichern">
        {{ speichernBusy ? 'Speichert…' : 'Speichern' }}
      </TheButton>
    </div>

    <!-- Odoo-Verbindung anlegen / aktualisieren / testen (PRD §4.7) -->
    <TheCard id="odoo-connection" titel="Odoo-Verbindung">
      <template #header>
        <div id="odoo-conn-head" class="flex items-center justify-between">
          <h3 class="text-sm font-semibold">Odoo-Verbindung</h3>
          <BadgePill
            id="odoo-conn-status"
            :tone="odooConfigured ? 'success' : 'muted'"
            :label="odooConfigured ? 'konfiguriert' : 'nicht konfiguriert'"
          />
        </div>
      </template>

      <div id="odoo-conn-form" class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div id="odoo-f-url">
          <label for="odoo-url" class="mb-1 block text-xs font-medium">Odoo-URL</label>
          <input id="odoo-url" v-model="odooForm.url" type="url" placeholder="https://…/odoo" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
        </div>
        <div id="odoo-f-db">
          <label for="odoo-db" class="mb-1 block text-xs font-medium">Datenbank</label>
          <input id="odoo-db" v-model="odooForm.db" type="text" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
        </div>
        <div id="odoo-f-user">
          <label for="odoo-username" class="mb-1 block text-xs font-medium">Benutzer</label>
          <input id="odoo-username" v-model="odooForm.username" type="text" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
        </div>
        <div id="odoo-f-key">
          <label for="odoo-apikey" class="mb-1 block text-xs font-medium">
            API-Key
            <span v-if="odooApiKeySet" class="font-normal text-muted-foreground">(gesetzt — leer lassen zum Beibehalten)</span>
          </label>
          <input id="odoo-apikey" v-model="odooForm.api_key" type="password" :placeholder="odooApiKeySet ? '•••••••• gesetzt' : ''" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
        </div>
        <div id="odoo-f-company">
          <label for="odoo-company" class="mb-1 block text-xs font-medium">Unternehmen (company_id)</label>
          <input id="odoo-company" v-model.number="odooForm.company_id" type="number" min="1" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
        </div>
        <div id="odoo-f-proto">
          <label for="odoo-protocol" class="mb-1 block text-xs font-medium">Protokoll</label>
          <select id="odoo-protocol" v-model="odooForm.protocol" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm">
            <option value="jsonrpc">JSON-RPC</option>
            <option value="xmlrpc">XML-RPC</option>
          </select>
        </div>
      </div>

      <!-- Testergebnis -->
      <div v-if="odooTestErgebnis" id="odoo-test-ok" class="mt-4">
        <Banner kind="info" titel="Verbindung erfolgreich">
          Server {{ odooTestErgebnis.server_version ?? '—' }} · uid {{ odooTestErgebnis.uid }} ·
          {{ odooTestErgebnis.latency_ms }} ms ·
          account.asset: {{ odooTestErgebnis.models['account.asset'] ? 'ja' : 'nein' }}
        </Banner>
      </div>
      <div v-if="odooTestFehler" id="odoo-test-fail" class="mt-4">
        <Banner kind="error" titel="Verbindung fehlgeschlagen">{{ odooTestFehler }}</Banner>
      </div>
      <p v-if="odooMsg" id="odoo-conn-msg" class="mt-3 text-sm text-primary">{{ odooMsg }}</p>

      <div id="odoo-conn-actions" class="mt-4 flex flex-wrap justify-end gap-3">
        <TheButton id="odoo-test-btn" variant="outline" size="lg" :disabled="odooBusy" @click="odooTesten">
          {{ odooBusy ? 'Bitte warten…' : 'Verbindung testen' }}
        </TheButton>
        <TheButton id="odoo-save-btn" variant="primary" size="lg" :disabled="odooBusy" @click="odooSpeichern">
          Verbindung speichern
        </TheButton>
      </div>
    </TheCard>
  </div>
</template>
