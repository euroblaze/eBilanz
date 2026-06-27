<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { formatEur, formatDate } from '@/libs/format'
import { useWjStore } from '@/stores/wj_store'
import { api, ApiError } from '@/libs/api'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'

// Kontennachweise (PRD §3.6) — Gruppen je Position aus Backend (/api/kontennachweise/{wj}).
const wj = useWjStore()

interface Konto {
  code: string
  name: string
  saldo: number
}
interface Position {
  id: string
  label: string
  status: 'vollständig' | 'fehlt'
  konten: Konto[]
}
interface Buchung {
  datum: Date
  beleg: string
  text: string
  betrag: number
}

const positionen = ref<Position[]>([])
const fehler = ref<string | null>(null)
async function laden() {
  try {
    positionen.value = (await api.kontennachweise(Number(wj.aktivesProjektId))) as Position[]
    fehler.value = null
    // Erstes Konto automatisch in der (dauerhaft offenen) Buchungen-Pane anzeigen.
    const ersteKonto = positionen.value.flatMap((p) => p.konten)[0] ?? null
    if (ersteKonto) drilldown(ersteKonto)
    else {
      aktivKonto.value = null
      buchungen.value = []
    }
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Kontennachweise konnten nicht geladen werden.'
  }
}
onMounted(laden)
watch(() => wj.aktivesProjektId, laden)

const nurLuecken = ref(false)
const sichtbare = computed(() =>
  nurLuecken.value ? positionen.value.filter((p) => p.status === 'fehlt') : positionen.value,
)
function summe(p: Position): number {
  return p.konten.reduce((a, k) => a + k.saldo, 0)
}

// Dauerhaft offene Buchungen-Pane — beim Klick auf „Buchungen" nur Werte aktualisieren.
const aktivKonto = ref<Konto | null>(null)
const buchungen = ref<Buchung[]>([])
async function drilldown(k: Konto) {
  aktivKonto.value = k
  buchungen.value = []
  try {
    const rows = await api.buchungen(Number(wj.aktivesProjektId), k.code)
    buchungen.value = rows.map((b) => ({ datum: new Date(b.datum), beleg: b.beleg, text: b.text, betrag: b.betrag }))
  } catch {
    buchungen.value = []
  }
}
</script>

<template>
  <div id="kontennachweise" class="space-y-4">
    <Banner v-if="fehler" id="kn-error" kind="error" titel="Kontennachweise konnten nicht geladen werden">
      {{ fehler }} — läuft das Backend?
    </Banner>

    <!-- CTAs -->
    <div id="kn-actions" class="flex flex-wrap items-center gap-3">
      <TheButton id="kn-generate" variant="primary">Nachweise generieren</TheButton>
      <TheButton id="kn-gaps" :variant="nurLuecken ? 'secondary' : 'outline'" @click="nurLuecken = !nurLuecken">
        {{ nurLuecken ? 'Alle anzeigen' : 'Lücken anzeigen' }}
      </TheButton>
      <TheButton id="kn-export" variant="ghost">Export (Prüfung)</TheButton>
    </div>

    <!-- Links: Gruppen · Rechts: dauerhaft offene Buchungen-Pane -->
    <div id="kn-grid" class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <!-- Gruppen je Taxonomie-Position -->
      <div id="kn-groups" class="space-y-4 lg:col-span-2">
        <TheCard v-for="p in sichtbare" :id="'kn-' + p.id" :key="p.id">
          <template #header>
            <div :id="'kn-head-' + p.id" class="flex items-center justify-between">
              <h3 class="text-sm font-semibold">{{ p.label }}</h3>
              <div class="flex items-center gap-3">
                <span class="text-sm font-medium tabular-nums">{{ formatEur(summe(p)) }}</span>
                <BadgePill :tone="p.status === 'vollständig' ? 'success' : 'danger'" :label="p.status" />
              </div>
            </div>
          </template>

          <!-- table-fixed + colgroup -> Saldo-Spalte über alle Gruppen identisch ausgerichtet -->
          <table :id="'kn-table-' + p.id" class="w-full table-fixed text-sm">
            <colgroup>
              <col style="width: 88px" />
              <col />
              <col style="width: 150px" />
              <col style="width: 116px" />
            </colgroup>
            <thead>
              <tr class="border-b border-border text-left text-xs text-muted-foreground">
                <th class="py-1.5 font-medium">Konto</th>
                <th class="py-1.5 font-medium">Bezeichnung</th>
                <th class="py-1.5 text-right font-medium">Saldo</th>
                <th class="py-1.5"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="k in p.konten" :id="'kn-row-' + p.id + '-' + k.code" :key="k.code" class="border-b border-border/60">
                <td class="py-1.5 font-mono text-xs">{{ k.code }}</td>
                <td class="truncate py-1.5">{{ k.name }}</td>
                <td class="py-1.5 text-right tabular-nums">{{ formatEur(k.saldo) }}</td>
                <td class="py-1.5 text-right">
                  <TheButton
                    variant="ghost"
                    :class="aktivKonto?.code === k.code ? 'text-primary' : ''"
                    @click="drilldown(k)"
                  >Buchungen</TheButton>
                </td>
              </tr>
            </tbody>
          </table>
        </TheCard>
      </div>

      <!-- Dauerhaft offene Buchungen-Pane (sticky) -->
      <aside id="kn-pane" class="lg:col-span-1">
        <TheCard
          id="kn-buchungen-card"
          class="lg:sticky lg:top-20"
          :titel="aktivKonto ? 'Buchungen · ' + aktivKonto.code : 'Buchungen'"
          :sub="aktivKonto ? aktivKonto.name : 'Konto links wählen'"
        >
          <table v-if="aktivKonto && buchungen.length" id="kn-buchungen" class="w-full table-fixed text-sm">
            <colgroup>
              <col style="width: 92px" />
              <col style="width: 84px" />
              <col />
              <col style="width: 116px" />
            </colgroup>
            <thead>
              <tr class="border-b border-border text-left text-xs text-muted-foreground">
                <th class="py-1.5 font-medium">Datum</th>
                <th class="py-1.5 font-medium">Beleg</th>
                <th class="py-1.5 font-medium">Text</th>
                <th class="py-1.5 text-right font-medium">Betrag</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(b, i) in buchungen" :id="'kn-b-' + i" :key="i" class="border-b border-border/60">
                <td class="py-1.5">{{ formatDate(b.datum) }}</td>
                <td class="py-1.5 font-mono text-xs">{{ b.beleg }}</td>
                <td class="truncate py-1.5">{{ b.text }}</td>
                <td class="py-1.5 text-right tabular-nums">{{ formatEur(b.betrag) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else id="kn-buchungen-empty" class="py-8 text-center text-sm text-muted-foreground">
            {{ aktivKonto ? 'Keine Buchungen.' : 'Auf „Buchungen" eines Kontos klicken.' }}
          </p>
        </TheCard>
      </aside>
    </div>
  </div>
</template>
