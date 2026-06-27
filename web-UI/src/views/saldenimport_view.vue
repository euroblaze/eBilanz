<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useWjStore } from '@/stores/wj_store'
import { formatEur, formatDate } from '@/libs/format'
import { api, ApiError } from '@/libs/api'
import BigPrompt from '@/components/ui/big_prompt.vue'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import DataGrid, { type GridColumn } from '@/components/ui/data_grid.vue'

// Saldenimport (PRD §3.3) — Salden aus Backend (/api/odoo/balances). Read-only Vorschau-DataGrid.
const wj = useWjStore()

type Diff = 'neu' | 'geaendert' | 'entfernt' | 'unveraendert'
interface Saldo {
  id: string
  code: string
  name: string
  account_type: string
  saldo: number
  soll_haben: 'S' | 'H'
  buchungen: number
  diff: Diff
}

// Filter-Card-Zustand
const kontenStatus = ref<'aktiv' | 'deprecated' | 'alle'>('aktiv')

// Salden aus dem Backend (kein Mock mehr)
const salden = ref<Saldo[]>([])
const abgerufen = ref(false) // false -> Empty-State (PRD §6)
const laden = ref(false)
const fehler = ref<string | null>(null)
const quelle = ref<string>('') // "odoo" | "demo"

// Salden des aktiven WJ laden (/api/odoo/balances?wj=).
async function loadBalances() {
  const id = Number(wj.aktivesProjektId)
  if (!Number.isFinite(id)) return
  laden.value = true
  fehler.value = null
  try {
    const res = await api.balances(id)
    salden.value = res.rows.map((r, i) => ({
      id: r.id ?? 'k-' + i,
      code: r.code,
      name: r.name,
      account_type: r.account_type,
      saldo: r.saldo,
      soll_haben: r.soll_haben,
      buchungen: r.buchungen,
      diff: (r.diff ?? 'unveraendert') as Diff, // Diff vs. zuletzt übernommenem Import (Backend)
    }))
    quelle.value = res.source
    abgerufen.value = true
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Salden konnten nicht geladen werden.'
    salden.value = []
    abgerufen.value = false
  } finally {
    laden.value = false
  }
}

onMounted(loadBalances)
// Bei WJ-Wechsel neu laden.
watch(() => wj.aktivesProjektId, loadBalances)

// Filter nach Kontoart (account_type) — clientseitig.
const kontoartFilter = ref<string>('alle')
const kontoarten = computed(() =>
  Array.from(new Set(salden.value.map((s) => s.account_type).filter(Boolean))).sort(),
)

const gefilterteSalden = computed(() =>
  kontoartFilter.value === 'alle'
    ? salden.value
    : salden.value.filter((s) => s.account_type === kontoartFilter.value),
)

// Diff-Zaehlung fuer Zusammenfassung
const diffCount = computed(() => {
  const c = { neu: 0, geaendert: 0, entfernt: 0 }
  for (const s of salden.value) if (s.diff !== 'unveraendert') c[s.diff]++
  return c
})

const columns: GridColumn[] = [
  { field: 'code', header: 'Konto', width: 110, sortable: true, filter: true, mono: true },
  { field: 'name', header: 'Bezeichnung', filter: true, sortable: true },
  { field: 'account_type', header: 'Kontoart', width: 170, filter: true, sortable: true },
  { field: 'saldo', header: 'Saldo (EUR)', width: 150, align: 'right', sortable: true, format: (v) => formatEur(Number(v)), footer: 'sum' },
  { field: 'soll_haben', header: 'S/H', width: 70 },
  { field: 'buchungen', header: '#Buchungen', width: 120, align: 'right', sortable: true, footer: 'sum' },
  { field: 'diff', header: 'Diff', width: 120 },
]

const DIFF_TONE = { neu: 'success', geaendert: 'warning', entfernt: 'danger' } as const
const DIFF_LABEL = { neu: 'neu', geaendert: 'geändert', entfernt: 'entfernt' } as const

function rowAccent(row: Saldo): string | undefined {
  if (row.diff === 'neu') return 'border-l-4 border-l-primary'
  if (row.diff === 'geaendert') return 'border-l-4 border-l-warning'
  if (row.diff === 'entfernt') return 'border-l-4 border-l-danger'
  return undefined
}

// CTAs
const hinweis = ref<string | null>(null)
function ausOdooAbrufen() {
  loadBalances()
}
function verwerfen() {
  salden.value = []
  abgerufen.value = false
}
// Aktuelle Salden als neuen Import-Baseline übernehmen -> Diff wird zurückgesetzt.
async function importUebernehmen() {
  const id = Number(wj.aktivesProjektId)
  if (!Number.isFinite(id)) return
  try {
    const res = await api.balancesUebernehmen(id)
    hinweis.value = `${res.uebernommen} Salden übernommen.`
    await loadBalances()
    setTimeout(() => (hinweis.value = null), 2600)
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Übernahme fehlgeschlagen.'
  }
}
</script>

<template>
  <div id="saldenimport" class="space-y-6">
    <!-- Fehler beim Laden -->
    <Banner v-if="fehler" id="import-error" kind="error" titel="Salden konnten nicht geladen werden">
      {{ fehler }} — läuft das Backend?
    </Banner>
    <Banner v-if="hinweis" id="import-hinweis" kind="info">{{ hinweis }}</Banner>

    <!-- Empty-State (PRD §6) -->
    <BigPrompt
      v-if="!abgerufen"
      id="import-empty"
      :titel="laden ? 'Salden werden geladen…' : 'Noch keine Salden'"
      :text="'Salden für ' + wj.aktivesProjekt.bezeichnung + ' aus Odoo abrufen.'"
    >
      <template #cta>
        <TheButton id="import-empty-cta" variant="primary" size="big" :disabled="laden" @click="ausOdooAbrufen">
          {{ laden ? 'Lädt…' : 'Salden aus Odoo abrufen' }}
        </TheButton>
      </template>
    </BigPrompt>

    <template v-else>
      <!-- Big-Prompt + Filter nebeneinander: 1 Zeile, 2 Spalten (separate Cards) -->
      <div id="import-overview" class="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2">
      <!-- Big-Prompt: Abruf + Periode -->
      <BigPrompt
        id="import-prompt"
        titel="Salden aus Odoo abrufen"
        :text="'Wirtschaftsjahr ' + formatDate(wj.aktivesProjekt.von) + ' – ' + formatDate(wj.aktivesProjekt.bis)"
      >
        <template #cta>
          <TheButton id="import-prompt-cta" variant="primary" size="big" @click="ausOdooAbrufen">
            Erneut abrufen
          </TheButton>
        </template>
      </BigPrompt>

      <!-- Filter-Card (PRD §3.3) -->
      <TheCard id="import-filter" titel="Filter">
        <div id="import-filter-row" class="flex flex-wrap items-center gap-4">
          <div id="import-filter-periode" class="text-sm">
            <span class="text-muted-foreground">WJ-Zeitraum: </span>
            <span class="font-medium">{{ formatDate(wj.aktivesProjekt.von) }} – {{ formatDate(wj.aktivesProjekt.bis) }}</span>
          </div>
          <BadgePill id="import-filter-posted" tone="muted" label="parent_state = posted (fix)" />
          <div id="import-filter-status" class="flex items-center gap-2 text-sm">
            <label for="import-konten-status" class="text-muted-foreground">Konten-Status</label>
            <select
              id="import-konten-status"
              v-model="kontenStatus"
              class="rounded-control border border-border bg-surface px-3 py-1.5 text-sm"
            >
              <option value="aktiv">aktiv</option>
              <option value="deprecated">deprecated</option>
              <option value="alle">alle</option>
            </select>
          </div>
          <!-- Filter nach Kontoart -->
          <div id="import-filter-kontoart" class="flex items-center gap-2 text-sm">
            <label for="import-kontoart" class="text-muted-foreground">Kontoart</label>
            <select
              id="import-kontoart"
              v-model="kontoartFilter"
              class="rounded-control border border-border bg-surface px-3 py-1.5 text-sm"
            >
              <option value="alle">alle</option>
              <option v-for="ka in kontoarten" :id="'kontoart-' + ka" :key="ka" :value="ka">{{ ka }}</option>
            </select>
          </div>
          <!-- Diff-Zusammenfassung vs. letztem Abruf -->
          <div id="import-diff-summary" class="ml-auto flex items-center gap-2">
            <BadgePill id="import-source" :tone="quelle === 'odoo' ? 'success' : 'info'" :label="'Quelle: ' + (quelle || '—')" />
            <BadgePill id="diff-neu" tone="success" :label="'neu: ' + diffCount.neu" />
            <BadgePill id="diff-geaendert" tone="warning" :label="'geändert: ' + diffCount.geaendert" />
            <BadgePill id="diff-entfernt" tone="danger" :label="'entfernt: ' + diffCount.entfernt" />
          </div>
        </div>
      </TheCard>
      </div>

      <!-- Vorschau-DataGrid (read-only) -->
      <DataGrid
        id="import-grid"
        :columns="columns"
        :data="gefilterteSalden"
        row-key="id"
        :row-accent="rowAccent"
      >
        <!-- S/H als Pill -->
        <template #cell-soll_haben="{ value }">
          <BadgePill :tone="value === 'S' ? 'info' : 'muted'" :label="value as string" />
        </template>
        <!-- Diff-Badge je Konto -->
        <template #cell-diff="{ row }">
          <BadgePill
            v-if="(row as Saldo).diff !== 'unveraendert'"
            :tone="DIFF_TONE[(row as Saldo).diff as keyof typeof DIFF_TONE]"
            :label="DIFF_LABEL[(row as Saldo).diff as keyof typeof DIFF_LABEL]"
          />
          <span v-else class="text-muted-foreground">—</span>
        </template>
      </DataGrid>

      <!-- CTAs (PRD §3.3) -->
      <div id="import-actions" class="flex flex-wrap justify-end gap-3">
        <TheButton id="import-discard" variant="ghost" size="lg" @click="verwerfen">Verwerfen</TheButton>
        <TheButton id="import-file" variant="outline" size="lg">Als Datei importieren</TheButton>
        <TheButton id="import-apply" variant="primary" size="lg" @click="importUebernehmen">Import übernehmen</TheButton>
      </div>
    </template>
  </div>
</template>
