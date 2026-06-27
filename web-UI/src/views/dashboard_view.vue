<script setup lang="ts">
import { computed } from 'vue'
import { useWjStore } from '@/stores/wj_store'
import { formatDateTime } from '@/libs/format'
import BigPrompt from '@/components/ui/big_prompt.vue'
import WorkflowStepper, { type Step } from '@/components/ui/workflow_stepper.vue'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'

// Dashboard (PRD §3.1) — Status des aktiven WJ + naechster Schritt. Mock-Daten.
const wj = useWjStore()

const steps: Step[] = [
  { nr: 1, label: 'Stammdaten', state: 'done' },
  { nr: 2, label: 'Import', state: 'done' },
  { nr: 3, label: 'Mapping', state: 'current' },
  { nr: 4, label: 'Erfassung', state: 'todo' },
  { nr: 5, label: 'Validierung', state: 'todo' },
  { nr: 6, label: 'Übermittlung', state: 'todo' },
]

// KPI-Cards (PRD §3.1)
const kpis = [
  { id: 'kpi-mapping', titel: 'Mapping-Quote', wert: '92 %', sub: '412/448 Konten', tone: 'info' as const },
  { id: 'kpi-mussfelder', titel: 'Offene Mussfelder', wert: '3', sub: 'Mapping abschließen', tone: 'warning' as const },
  { id: 'kpi-fehler', titel: 'Validierungsfehler', wert: '0', sub: 'keine Fehler', tone: 'success' as const },
  { id: 'kpi-uebermittlung', titel: 'Letzte Übermittlung', wert: '—', sub: 'noch nicht gesendet', tone: 'muted' as const },
]

// Datenquelle-Status (PRD §3.1)
const letzterAbruf = formatDateTime(new Date(2026, 5, 26, 14, 12))

// Aktivitaets-Feed (Mock)
const feed = [
  { id: 'feed-1', wer: 'S. Bauer', was: 'Mapping-Vorschläge übernommen (28 Konten)', wann: formatDateTime(new Date(2026, 5, 26, 14, 20)) },
  { id: 'feed-2', wer: 'System', was: 'Salden aus Odoo abgerufen', wann: formatDateTime(new Date(2026, 5, 26, 14, 12)) },
  { id: 'feed-3', wer: 'S. Bauer', was: 'Stammdaten gespeichert', wann: formatDateTime(new Date(2026, 5, 25, 9, 3)) },
]

const naechsteAktion = computed(
  () => `${wj.aktivesProjekt.bezeichnung}: 3 Mussfelder offen → Konten-Mapping abschließen`,
)
</script>

<template>
  <div id="dashboard" class="space-y-6">
    <!-- Big-Prompt + Workflow-Stepper: 1 Zeile, 2 Spalten -->
    <div id="dashboard-top-row" class="grid grid-cols-1 items-stretch gap-6 lg:grid-cols-2">
      <!-- Big-Prompt: aktueller WJ + naechste Aktion -->
      <BigPrompt id="dashboard-prompt" titel="Nächster Schritt" :text="naechsteAktion">
        <template #cta>
          <TheButton id="dashboard-prompt-cta" variant="primary" size="big">Zum Konten-Mapping</TheButton>
        </template>
      </BigPrompt>

      <!-- Workflow-Stepper -->
      <TheCard id="dashboard-stepper-card" titel="Workflow">
        <WorkflowStepper id="dashboard-stepper" :steps="steps" />
      </TheCard>
    </div>

    <!-- KPI-Grid (4er) -->
    <div id="dashboard-kpis" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <TheCard v-for="k in kpis" :id="k.id" :key="k.id">
        <p class="text-xs font-medium text-muted-foreground">{{ k.titel }}</p>
        <p class="mt-1 text-3xl font-bold text-foreground">{{ k.wert }}</p>
        <BadgePill :id="k.id + '-pill'" :tone="k.tone" :label="k.sub" class="mt-2" />
      </TheCard>
    </div>

    <div id="dashboard-bottom" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <!-- Datenquelle-Status -->
      <TheCard id="dashboard-quelle" titel="Datenquelle">
        <dl id="dashboard-quelle-list" class="space-y-2 text-sm">
          <div class="flex justify-between">
            <dt class="text-muted-foreground">Odoo-Verbindung</dt>
            <dd><BadgePill id="quelle-odoo" :tone="wj.odooVerbunden ? 'success' : 'danger'" :label="wj.odooVerbunden ? 'verbunden' : 'getrennt'" /></dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">Letzter Saldenabruf</dt>
            <dd class="font-medium">{{ letzterAbruf }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">ERiC-Version</dt>
            <dd class="font-medium">{{ wj.ericVersion }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">Taxonomie</dt>
            <dd class="font-medium">{{ wj.aktivesProjekt.taxonomieLabel }}</dd>
          </div>
        </dl>
      </TheCard>

      <!-- Aktivitaets-Feed -->
      <TheCard id="dashboard-feed" titel="Aktivität">
        <ul id="dashboard-feed-list" class="space-y-3">
          <li v-for="f in feed" :id="f.id" :key="f.id" class="flex items-start gap-3 text-sm">
            <span class="mt-1.5 h-2 w-2 shrink-0 rounded-pill bg-primary" />
            <div>
              <p class="text-foreground"><span class="font-semibold">{{ f.wer }}</span> — {{ f.was }}</p>
              <p class="text-xs text-muted-foreground">{{ f.wann }}</p>
            </div>
          </li>
        </ul>
      </TheCard>
    </div>
  </div>
</template>
