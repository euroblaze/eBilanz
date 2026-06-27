<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Lock } from 'lucide-vue-next'
import { useWjStore } from '@/stores/wj_store'
import { formatEur } from '@/libs/format'
import { api, ApiError } from '@/libs/api'
import BigPrompt from '@/components/ui/big_prompt.vue'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import SplitPane from '@/components/ui/split_pane.vue'
import DataGrid, { type GridColumn } from '@/components/ui/data_grid.vue'
import TaxonomyTree, { type TaxNode } from '@/components/ui/taxonomy_tree.vue'

// Konten-Mapping (PRD §3.4) — Split-Pane: links Odoo-Konten, rechts Taxonomie-Positionen.
const wj = useWjStore()

// --- Taxonomie + Konten aus Backend (/api/mapping/{wj}) ---------------------
const taxonomy = ref<TaxNode[]>([])

interface Leaf { id: string; label: string; feldtyp?: string }
function flattenLeaves(nodes: TaxNode[]): Leaf[] {
  const out: Leaf[] = []
  const walk = (ns: TaxNode[]) => {
    for (const n of ns) {
      if (n.children?.length) walk(n.children)
      else out.push({ id: n.id, label: n.label, feldtyp: n.feldtyp })
    }
  }
  walk(nodes)
  return out
}
const leaves = computed(() => flattenLeaves(taxonomy.value))
const mussfeldLeaves = computed(() => leaves.value.filter((l) => l.feldtyp === 'Mussfeld'))

type Status = 'nicht zugeordnet' | 'zugeordnet' | 'Auffangposition' | 'Konflikt'
interface MapAccount {
  id: string // = account_key
  code: string
  name: string
  saldo: number
  account_type: string
  mapping_status: Status
  assignedPositionId?: string
  assignedPositionLabel?: string
  suggestion?: { positionId: string; label: string; confidence: number }
}

const accounts = ref<MapAccount[]>([])
const ladeFehler = ref<string | null>(null)

async function laden() {
  try {
    const res = await api.mapping(Number(wj.aktivesProjektId))
    taxonomy.value = res.positions as TaxNode[]
    accounts.value = res.accounts.map((a) => ({
      id: a.account_key,
      code: a.code,
      name: a.name,
      saldo: a.saldo,
      account_type: a.account_type,
      mapping_status: a.status as Status,
      assignedPositionId: a.position_id ?? undefined,
      assignedPositionLabel: a.position_label ?? undefined,
      suggestion: a.suggestion
        ? { positionId: a.suggestion.position_id, label: a.suggestion.label, confidence: a.suggestion.confidence }
        : undefined,
    }))
    selected.clear()
    ladeFehler.value = null
  } catch (e) {
    ladeFehler.value = e instanceof ApiError ? e.message : 'Mapping konnte nicht geladen werden.'
  }
}
onMounted(laden)
watch(() => wj.aktivesProjektId, laden)

// --- Auswahl + Filter -------------------------------------------------------
const selected = reactive(new Set<string>())
const nurOffene = ref(false)
const suche = ref('')
const kontenrahmen = ref<'SKR03' | 'SKR04'>('SKR04')

const sichtbareKonten = computed(() =>
  nurOffene.value
    ? accounts.value.filter((a) => a.mapping_status === 'nicht zugeordnet' || a.mapping_status === 'Konflikt')
    : accounts.value,
)

function toggleSelect(id: string) {
  if (selected.has(id)) selected.delete(id)
  else selected.add(id)
}
function alleWaehlen() {
  sichtbareKonten.value.forEach((a) => selected.add(a.id))
}
function auswahlAufheben() {
  selected.clear()
}

// Offene Mussfelder (Big-Prompt §3.4)
const zugeordnetePositionen = computed(() => new Set(accounts.value.map((a) => a.assignedPositionId).filter(Boolean)))
const offeneMussfelder = computed(() => mussfeldLeaves.value.filter((l) => !zugeordnetePositionen.value.has(l.id)))

// --- Hinweis / Toast (leichtgewichtig) --------------------------------------
const notice = ref<{ kind: 'info' | 'success' | 'error'; text: string } | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined
function zeigeHinweis(kind: 'info' | 'success' | 'error', text: string) {
  notice.value = { kind, text }
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => (notice.value = null), 3000)
}

// --- Zuordnung --------------------------------------------------------------
function positionZuweisen(node: TaxNode) {
  // Regel: direkte Zuordnung auf Summenmussfeld / Knoten blockiert (PRD §3.4)
  if (node.feldtyp === 'Summenmussfeld' || node.children?.length) {
    zeigeHinweis('error', 'Direkte Zuordnung auf Summenmussfeld nicht möglich — Unterposition oder Auffangposition wählen.')
    return
  }
  if (selected.size === 0) {
    zeigeHinweis('info', 'Bitte links zuerst Konten auswählen.')
    return
  }
  let n = 0
  for (const a of accounts.value) {
    if (!selected.has(a.id)) continue
    a.assignedPositionId = node.id
    a.assignedPositionLabel = node.label
    a.mapping_status = node.feldtyp === 'Auffangposition' ? 'Auffangposition' : 'zugeordnet'
    n++
  }
  selected.clear()
  zeigeHinweis('success', `${n} Konto/Konten → ${node.label} zugeordnet.`)
}

function vorschlaegeUebernehmen() {
  let n = 0
  for (const a of accounts.value) {
    if (a.mapping_status !== 'nicht zugeordnet' || !a.suggestion) continue
    const leaf = leaves.value.find((l) => l.id === a.suggestion!.positionId)
    if (!leaf || leaf.feldtyp === 'Summenmussfeld') continue
    a.assignedPositionId = leaf.id
    a.assignedPositionLabel = leaf.label
    a.mapping_status = leaf.feldtyp === 'Auffangposition' ? 'Auffangposition' : 'zugeordnet'
    n++
  }
  zeigeHinweis('success', `${n} Vorschlag/Vorschläge übernommen.`)
}

function zuruecksetzen() {
  const ids = selected.size ? selected : new Set(accounts.value.map((a) => a.id))
  let n = 0
  for (const a of accounts.value) {
    if (!ids.has(a.id)) continue
    a.assignedPositionId = undefined
    a.assignedPositionLabel = undefined
    a.mapping_status = 'nicht zugeordnet'
    n++
  }
  selected.clear()
  zeigeHinweis('info', `${n} Zuordnung(en) zurückgesetzt.`)
}

async function mappingSpeichern() {
  try {
    await api.saveMapping(
      Number(wj.aktivesProjektId),
      accounts.value.map((a) => ({
        account_key: a.id,
        position_id: a.assignedPositionId ?? null,
        position_label: a.assignedPositionLabel ?? null,
        status: a.mapping_status,
      })),
    )
    zeigeHinweis('success', `Mapping gespeichert (${kontenrahmen.value}, Taxonomie ${wj.aktivesProjekt.taxonomieVersion}).`)
  } catch (e) {
    zeigeHinweis('error', e instanceof ApiError ? e.message : 'Speichern fehlgeschlagen.')
  }
}

// --- Grid -------------------------------------------------------------------
const STATUS_TONE: Record<Status, 'muted' | 'success' | 'info' | 'danger'> = {
  'nicht zugeordnet': 'muted',
  zugeordnet: 'success',
  Auffangposition: 'info',
  Konflikt: 'danger',
}
const columns: GridColumn[] = [
  { field: 'select', header: '', width: 44 },
  { field: 'code', header: 'Konto', width: 90, sortable: true, filter: true, mono: true },
  { field: 'name', header: 'Bezeichnung', filter: true, sortable: true },
  { field: 'saldo', header: 'Saldo', width: 130, align: 'right', sortable: true, format: (v) => formatEur(Number(v)) },
  { field: 'mapping_status', header: 'Status', width: 150 },
  { field: 'zuordnung', header: 'Zuordnung / Vorschlag', width: 220 },
]
function rowAccent(row: MapAccount): string | undefined {
  if (row.mapping_status === 'Konflikt') return 'border-l-4 border-l-danger'
  if (row.mapping_status === 'zugeordnet') return 'border-l-4 border-l-primary'
  if (row.mapping_status === 'Auffangposition') return 'border-l-4 border-l-warning'
  return undefined
}
</script>

<template>
  <div id="mapping" class="space-y-4">
    <Banner v-if="ladeFehler" id="mapping-error" kind="error" titel="Mapping konnte nicht geladen werden">
      {{ ladeFehler }} — läuft das Backend?
    </Banner>

    <!-- Big-Prompt + Steuerleiste: 1 Zeile, 2 Spalten -->
    <div id="mapping-top-row" class="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2">
    <!-- Big-Prompt bei unzugeordneten Mussfeldern (PRD §3.4) -->
    <BigPrompt
      v-if="offeneMussfelder.length"
      id="mapping-prompt"
      :titel="offeneMussfelder.length + ' Mussfeld-Positionen noch ohne Konto'"
      text="Ordnen Sie die offenen Pflichtpositionen zu, bevor Sie validieren."
    >
      <template #cta>
        <TheButton id="mapping-prompt-cta" variant="primary" size="big" @click="nurOffene = true">
          Offene anzeigen
        </TheButton>
      </template>
    </BigPrompt>

    <!-- Steuerleiste: Mapping-Set + CTAs (PRD §3.4 / §5) -->
    <!-- Ohne offene Mussfelder entfaellt der Big-Prompt -> Steuerleiste volle Breite -->
    <TheCard id="mapping-controls" :class="offeneMussfelder.length ? '' : 'lg:col-span-2'">
      <div id="mapping-controls-row" class="flex h-full flex-wrap items-center gap-3">
        <div id="mapping-set" class="flex items-center gap-2 text-sm">
          <label for="mapping-kontenrahmen" class="text-muted-foreground">Kontenrahmen</label>
          <select id="mapping-kontenrahmen" v-model="kontenrahmen" class="rounded-control border border-border bg-surface px-3 py-1.5 text-sm">
            <option value="SKR03">SKR03</option>
            <option value="SKR04">SKR04</option>
          </select>
        </div>
        <BadgePill id="mapping-tax" tone="info" :label="'Taxonomie ' + wj.aktivesProjekt.taxonomieVersion" />
        <div id="mapping-controls-spacer" class="ml-auto flex flex-wrap items-center gap-2">
          <TheButton id="mapping-only-open" :variant="nurOffene ? 'secondary' : 'ghost'" @click="nurOffene = !nurOffene">
            {{ nurOffene ? 'Alle anzeigen' : 'Offene anzeigen' }}
          </TheButton>
          <TheButton id="mapping-apply-suggestions" variant="outline" @click="vorschlaegeUebernehmen">Vorschläge übernehmen</TheButton>
          <TheButton id="mapping-save" variant="primary" @click="mappingSpeichern">Mapping speichern</TheButton>
        </div>
      </div>
    </TheCard>
    </div>

    <!-- Split-Pane: Konten | Positionen -->
    <SplitPane id="mapping-split">
      <template #left>
        <TheCard id="mapping-accounts" titel="Odoo-Konten" :sub="selected.size + ' ausgewählt'">
          <template #header>
            <div id="mapping-bulk" class="flex items-center justify-between">
              <h3 class="text-sm font-semibold">Odoo-Konten <span class="font-normal text-muted-foreground">· {{ selected.size }} ausgewählt</span></h3>
              <div id="mapping-bulk-actions" class="flex gap-1">
                <TheButton id="mapping-select-all" variant="ghost" @click="alleWaehlen">Alle wählen</TheButton>
                <TheButton id="mapping-clear" variant="ghost" @click="auswahlAufheben">Aufheben</TheButton>
                <TheButton id="mapping-reset" variant="ghost" @click="zuruecksetzen">Zurücksetzen</TheButton>
              </div>
            </div>
          </template>

          <DataGrid id="mapping-grid" :columns="columns" :data="sichtbareKonten" row-key="id" :row-accent="rowAccent" max-height="58vh">
            <template #cell-select="{ row }">
              <input
                :id="'sel-' + (row as MapAccount).id"
                type="checkbox"
                class="h-4 w-4 accent-primary"
                :checked="selected.has((row as MapAccount).id)"
                @change="toggleSelect((row as MapAccount).id)"
              />
            </template>
            <template #cell-mapping_status="{ row }">
              <BadgePill :tone="STATUS_TONE[(row as MapAccount).mapping_status]" :label="(row as MapAccount).mapping_status" />
            </template>
            <template #cell-zuordnung="{ row }">
              <span v-if="(row as MapAccount).assignedPositionLabel" class="truncate text-primary">
                {{ (row as MapAccount).assignedPositionLabel }}
              </span>
              <BadgePill
                v-else-if="(row as MapAccount).suggestion"
                tone="warning"
                :label="'Vorschlag: ' + (row as MapAccount).suggestion!.label + ' (' + (row as MapAccount).suggestion!.confidence + '%)'"
              />
              <span v-else class="text-muted-foreground">—</span>
            </template>
          </DataGrid>
        </TheCard>
      </template>

      <template #right>
        <TheCard id="mapping-positions" titel="Taxonomie-Positionen">
          <div id="mapping-pos-search" class="mb-3">
            <input
              id="mapping-search"
              v-model="suche"
              type="text"
              placeholder="Position suchen…"
              class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm"
            />
          </div>
          <Banner id="mapping-hint" kind="info" class="mb-3">
            Konten links auswählen, dann rechts eine Position anklicken. Summenmussfelder
            <Lock class="inline h-3.5 w-3.5 align-text-bottom" /> sind gesperrt.
          </Banner>
          <div id="mapping-tree-wrap" class="max-h-[52vh] overflow-auto">
            <TaxonomyTree id="mapping-tree" :nodes="taxonomy" :search="suche" @select="positionZuweisen" />
          </div>
        </TheCard>
      </template>
    </SplitPane>

    <!-- Toast/Hinweis -->
    <Transition name="fade">
      <div
        v-if="notice"
        id="mapping-notice"
        class="fixed bottom-6 right-6 z-50 max-w-sm rounded-control px-4 py-3 text-sm text-white shadow-pop"
        :class="notice.kind === 'error' ? 'bg-danger' : notice.kind === 'success' ? 'bg-primary' : 'bg-foreground'"
      >
        {{ notice.text }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
