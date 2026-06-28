<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWjStore } from '@/stores/wj_store'
import { api, ApiError } from '@/libs/api'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import Banner from '@/components/ui/banner.vue'
import GaapGrid, { type GaapNode } from '@/components/ui/gaap_grid.vue'

// E-Bilanz Erfassung (PRD §3.5) — tree-grid Maske je Bestandteil, Werte aus Backend.
const route = useRoute()
const router = useRouter()
const wj = useWjStore()

// Bestandteile (PRD §2.2 children). available: Verfügbarkeit (Mock-Bedingungen §3.5).
interface BestandteilMeta {
  key: string
  label: string
  available: boolean
  hinweis?: string
  warnung?: string
}
const BESTANDTEILE: BestandteilMeta[] = [
  { key: 'bilanz', label: 'Bilanz', available: true },
  { key: 'guv', label: 'Gewinn- und Verlustrechnung', available: true },
  { key: 'ergebnisverwendung', label: 'Ergebnisverwendung', available: true, hinweis: 'Nur Kapitalgesellschaft (GmbH aktiv).' },
  { key: 'steuerlich', label: 'Steuerliche Gewinnermittlung', available: true },
  { key: 'ueberleitung', label: 'Überleitungsrechnung', available: false, hinweis: 'Nur bei Bilanzierungsstandard „Handelsrecht“.' },
  { key: 'anlagenspiegel', label: 'Anlagenspiegel', available: true, hinweis: 'Anlagevermögen live aus der Odoo-Anlagenbuchhaltung (account.asset); Sonderposten manuell.' },
]

const aktiv = computed(() => (route.params.bestandteil as string) || 'bilanz')
const aktivMeta = computed(() => BESTANDTEILE.find((b) => b.key === aktiv.value) ?? BESTANDTEILE[0])

function wechsle(key: string) {
  router.push('/gaap/' + key)
}

// Erfassungsbaum des aktiven Bestandteils aus dem Backend.
const nodes = ref<GaapNode[]>([])
const laden = ref(false)
const fehler = ref<string | null>(null)

async function ladenBestandteil() {
  laden.value = true
  fehler.value = null
  try {
    const res = await api.gaap(Number(wj.aktivesProjektId), aktiv.value)
    nodes.value = res.nodes as GaapNode[]
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Erfassung konnte nicht geladen werden.'
    nodes.value = []
  } finally {
    laden.value = false
  }
}
onMounted(ladenBestandteil)
watch([aktiv, () => wj.aktivesProjektId], ladenBestandteil)

function flatten(ns: GaapNode[]): GaapNode[] {
  const out: GaapNode[] = []
  const walk = (xs: GaapNode[]) => xs.forEach((n) => { out.push(n); if (n.children) walk(n.children) })
  walk(ns)
  return out
}

const notice = ref<string | null>(null)
async function speichern() {
  const leaves = flatten(nodes.value).filter((n) => !n.children?.length)
  try {
    await api.saveGaap(
      Number(wj.aktivesProjektId),
      aktiv.value,
      leaves.map((n) => ({ position_id: n.id, wert_final: n.wertFinal ?? null, nil: !!n.nil })),
    )
    notice.value = 'Erfassung gespeichert.'
  } catch (e) {
    notice.value = e instanceof ApiError ? e.message : 'Speichern fehlgeschlagen.'
  }
  setTimeout(() => (notice.value = null), 2500)
}
function neuBerechnen() {
  for (const n of flatten(nodes.value)) {
    n.wertFinal = null
    n.nil = false
  }
  notice.value = 'Aus Mapping neu berechnet (Erfasste Werte zurückgesetzt).'
  setTimeout(() => (notice.value = null), 2500)
}
function geprueft() {
  notice.value = 'Als geprüft markiert (Vier-Augen).'
  setTimeout(() => (notice.value = null), 2500)
}
</script>

<template>
  <div id="gaap" class="space-y-4">
    <!-- Bestandteil-Tabs -->
    <div id="gaap-tabs" class="flex flex-wrap gap-1 border-b border-border">
      <button
        v-for="b in BESTANDTEILE"
        :id="'gaap-tab-' + b.key"
        :key="b.key"
        type="button"
        class="rounded-t-control px-3 py-2 text-sm"
        :class="[
          aktiv === b.key ? 'border-b-2 border-primary font-semibold text-primary' : 'text-muted-foreground hover:text-foreground',
          !b.available ? 'opacity-40' : '',
        ]"
        :disabled="!b.available"
        @click="wechsle(b.key)"
      >
        {{ b.label }}
      </button>
    </div>

    <Banner v-if="fehler" id="gaap-error" kind="error">{{ fehler }} — läuft das Backend?</Banner>
    <Banner v-if="notice" id="gaap-notice" kind="info">{{ notice }}</Banner>
    <Banner v-if="aktivMeta.warnung" id="gaap-warn" kind="warning">{{ aktivMeta.warnung }}</Banner>
    <Banner v-if="aktivMeta.hinweis" id="gaap-hint" kind="info">{{ aktivMeta.hinweis }}</Banner>

    <!-- Tree-Grid oder Leerzustand -->
    <p v-if="laden" id="gaap-loading" class="py-6 text-center text-sm text-muted-foreground">Lädt…</p>
    <GaapGrid v-else-if="nodes.length > 0" :id="'gaap-grid-' + aktiv" :nodes="nodes" />
    <TheCard v-else id="gaap-empty">
      <p class="py-6 text-center text-sm text-muted-foreground">Für diesen Bestandteil sind keine Positionen verfügbar.</p>
    </TheCard>

    <!-- CTAs (PRD §3.5) -->
    <div id="gaap-actions" class="flex flex-wrap justify-end gap-3">
      <TheButton id="gaap-recalc" variant="outline" size="lg" @click="neuBerechnen">Aus Mapping neu berechnen</TheButton>
      <TheButton id="gaap-checked" variant="secondary" size="lg" @click="geprueft">Als geprüft markieren</TheButton>
      <TheButton id="gaap-save" variant="primary" size="lg" @click="speichern">Speichern</TheButton>
    </div>
  </div>
</template>
