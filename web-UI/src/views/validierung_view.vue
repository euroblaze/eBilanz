<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/libs/format'
import { useWjStore } from '@/stores/wj_store'
import { api, ApiError } from '@/libs/api'
import BigPrompt from '@/components/ui/big_prompt.vue'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import DataGrid, { type GridColumn } from '@/components/ui/data_grid.vue'

// Validierung (PRD §3.7) — ERiC-Prüfungen über Backend (/api/validierung/{wj}).
const router = useRouter()
const wj = useWjStore()

type Schwere = 'Fehler' | 'Hinweis'
interface Pruefmeldung {
  id: string
  schwere: Schwere
  code: string
  position: string
  meldung: string
  route: string // Ziel fuer Click-to-field
}

const geprueft = ref(false)
const letzterCheck = ref<Date | null>(null)
const meldungen = ref<Pruefmeldung[]>([])
const laden = ref(false)
const fehler = ref<string | null>(null)

const fehlerCount = computed(() => meldungen.value.filter((m) => m.schwere === 'Fehler').length)
const hinweisCount = computed(() => meldungen.value.filter((m) => m.schwere === 'Hinweis').length)
const ampel = computed<'success' | 'warning' | 'danger'>(() =>
  fehlerCount.value > 0 ? 'danger' : hinweisCount.value > 0 ? 'warning' : 'success',
)
const ampelText = computed(() =>
  fehlerCount.value > 0 ? 'Validierung fehlerhaft' : hinweisCount.value > 0 ? 'Mit Hinweisen' : 'Validiert OK',
)

async function pruefen() {
  laden.value = true
  fehler.value = null
  try {
    const res = await api.validieren(Number(wj.aktivesProjektId))
    meldungen.value = res.meldungen
    letzterCheck.value = new Date(res.geprueft_am)
    geprueft.value = true
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Validierung fehlgeschlagen.'
  } finally {
    laden.value = false
  }
}
onMounted(pruefen)
watch(() => wj.aktivesProjektId, pruefen)

const columns: GridColumn[] = [
  { field: 'schwere', header: 'Schwere', width: 110 },
  { field: 'code', header: 'ERiC-Code', width: 130, mono: true, filter: true },
  { field: 'position', header: 'Position/Feld', filter: true },
  { field: 'meldung', header: 'Meldung', filter: true },
  { field: 'aktion', header: '', width: 130 },
]
</script>

<template>
  <div id="validierung" class="space-y-6">
    <Banner v-if="fehler" id="val-error" kind="error" titel="Validierung fehlgeschlagen">
      {{ fehler }} — läuft das Backend?
    </Banner>

    <!-- Big-Prompt + Ergebnis: 1 Zeile, 2 Spalten -->
    <div id="val-top-row" class="grid grid-cols-1 items-stretch gap-6 md:grid-cols-2">
      <!-- Big-Prompt: ERiC-Prüfung -->
      <BigPrompt
        id="val-prompt"
        titel="Jetzt mit ERiC prüfen"
        :text="letzterCheck ? 'Letzte Prüfung: ' + formatDateTime(letzterCheck) : 'Noch nicht geprüft'"
      >
        <template #cta>
          <TheButton id="val-prompt-cta" variant="primary" size="big" :disabled="laden" @click="pruefen">
            {{ laden ? 'Prüft…' : geprueft ? 'Erneut prüfen' : 'Jetzt mit ERiC prüfen' }}
          </TheButton>
        </template>
      </BigPrompt>

      <!-- Ergebnis-Card: Ampel + Zähler -->
      <TheCard id="val-result">
        <div id="val-result-row" class="flex h-full flex-wrap items-center gap-4">
          <span id="val-ampel" class="h-4 w-4 rounded-pill" :class="ampel === 'danger' ? 'bg-danger' : ampel === 'warning' ? 'bg-warning' : 'bg-primary'" />
          <span id="val-ampel-text" class="text-lg font-bold">{{ ampelText }}</span>
          <div id="val-counts" class="ml-auto flex items-center gap-2">
            <BadgePill id="val-fehler" tone="danger" :label="fehlerCount + ' Fehler'" />
            <BadgePill id="val-hinweis" tone="warning" :label="hinweisCount + ' Hinweise'" />
          </div>
        </div>
      </TheCard>
    </div>

    <!-- Fehler-DataGrid mit Click-to-field -->
    <DataGrid id="val-grid" :columns="columns" :data="meldungen" row-key="id" max-height="48vh">
      <template #cell-schwere="{ row }">
        <BadgePill :tone="(row as Pruefmeldung).schwere === 'Fehler' ? 'danger' : 'warning'" :label="(row as Pruefmeldung).schwere" />
      </template>
      <template #cell-aktion="{ row }">
        <TheButton variant="ghost" @click="router.push((row as Pruefmeldung).route)">Zum Feld</TheButton>
      </template>
    </DataGrid>

    <!-- CTAs -->
    <div id="val-actions" class="flex flex-wrap justify-end gap-3">
      <TheButton id="val-recheck" variant="outline" size="lg" @click="pruefen">Erneut prüfen</TheButton>
      <TheButton id="val-export" variant="ghost" size="lg">Bericht exportieren</TheButton>
      <TheButton
        id="val-next"
        variant="primary"
        size="lg"
        :disabled="fehlerCount > 0"
        @click="router.push('/uebermittlung')"
      >
        Weiter zur Übermittlung
      </TheButton>
    </div>
  </div>
</template>
