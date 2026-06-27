<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWjStore } from '@/stores/wj_store'
import { formatEur } from '@/libs/format'
import { api, ApiError } from '@/libs/api'
import TheCard from '@/components/ui/the_card.vue'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import WorkflowStepper, { type Step } from '@/components/ui/workflow_stepper.vue'

// Übermittlung (PRD §3.8) — Stepper-Wizard. Echtfall-Guard (§7). Mock.
const router = useRouter()
const wj = useWjStore()

const aktuell = ref(1) // 1..4
const STEP_TITEL = ['Vorschau', 'Zertifikat', 'Modus', 'Bestätigung']
const steps = computed<Step[]>(() =>
  STEP_TITEL.map((label, i) => ({
    nr: i + 1,
    label,
    state: aktuell.value === i + 1 ? 'current' : aktuell.value > i + 1 ? 'done' : 'todo',
  })),
)

// Guard-Eingaben (§7: kann_echtfall = validierung_ok && zertifikat && hersteller_id && freigabe)
const validierungOk = ref(true) // aus Validierung übernommen (Mock)
const herstellerId = ref(true)
const zertifikat = ref('')
const pin = ref('')
const modus = ref<'test' | 'echt'>('test')
const freigabeErteilt = ref(false)
const gesendet = ref(false)

const kannEchtfall = computed(
  () => validierungOk.value && !!zertifikat.value && herstellerId.value && freigabeErteilt.value,
)

// Mock-Vorschau
const vorschau = { bilanzsumme: 1284500.55, jahresueberschuss: 96420.18 }
const xbrlPreview = `<xbrli:xbrl>\n  <gcd:Bericht WJ="${wj.aktivesProjekt.bezeichnung}" Taxonomie="${wj.aktivesProjekt.taxonomieVersion}"/>\n  <de-gaap:BilanzAktivaSumme>${vorschau.bilanzsumme}</de-gaap:BilanzAktivaSumme>\n</xbrli:xbrl>`

const notice = ref<string | null>(null)
function weiter() {
  if (aktuell.value < 4) aktuell.value++
}
function zurueck() {
  if (aktuell.value > 1) aktuell.value--
}
async function senden(art: 'test' | 'echt') {
  if (art === 'echt' && !kannEchtfall.value) return
  try {
    const res = await api.uebermitteln(Number(wj.aktivesProjektId), art)
    gesendet.value = true
    notice.value =
      (art === 'echt' ? 'Echtfall übermittelt' : 'Testfall gesendet') +
      ' — Transfer-Ticket ' + res.transfer_ticket
    setTimeout(() => router.push('/protokoll'), 1500)
  } catch (e) {
    notice.value = e instanceof ApiError ? e.message : 'Übermittlung fehlgeschlagen.'
  }
}
</script>

<template>
  <div id="uebermittlung" class="space-y-6">
    <Banner v-if="gesendet" id="ueb-sent" kind="info" titel="Versand erfolgreich">
      {{ notice }} Weiterleitung zum Protokoll…
    </Banner>

    <TheCard id="ueb-stepper-card">
      <WorkflowStepper id="ueb-stepper" :steps="steps" />
    </TheCard>

    <!-- Schritt 1: Vorschau -->
    <TheCard v-if="aktuell === 1" id="ueb-step1" titel="Vorschau">
      <div id="ueb-preview" class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div id="ueb-preview-kpi" class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-muted-foreground">Wirtschaftsjahr</span><span class="font-medium">{{ wj.aktivesProjekt.bezeichnung }}</span></div>
          <div class="flex justify-between"><span class="text-muted-foreground">Bilanzsumme</span><span class="font-medium">{{ formatEur(vorschau.bilanzsumme) }}</span></div>
          <div class="flex justify-between"><span class="text-muted-foreground">Jahresüberschuss</span><span class="font-medium">{{ formatEur(vorschau.jahresueberschuss) }}</span></div>
          <div class="flex justify-between"><span class="text-muted-foreground">Taxonomie</span><span class="font-medium">{{ wj.aktivesProjekt.taxonomieLabel }}</span></div>
        </div>
        <div id="ueb-preview-xbrl">
          <p class="mb-1 text-xs font-medium text-muted-foreground">XBRL-Vorschau</p>
          <pre id="ueb-xbrl" class="overflow-auto rounded-control border border-border bg-muted p-3 font-mono text-xs">{{ xbrlPreview }}</pre>
        </div>
      </div>
    </TheCard>

    <!-- Schritt 2: Zertifikat -->
    <TheCard v-if="aktuell === 2" id="ueb-step2" titel="Zertifikat">
      <div id="ueb-cert" class="max-w-md space-y-3">
        <div>
          <label for="ueb-cert-select" class="mb-1 block text-xs font-medium">Zertifikat</label>
          <select id="ueb-cert-select" v-model="zertifikat" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm">
            <option value="">— wählen —</option>
            <option value="steuerberater.pfx">Steuerberater Müller (gültig bis 2027)</option>
            <option value="firma.pfx">Muster GmbH (gültig bis 2026)</option>
          </select>
        </div>
        <div>
          <label for="ueb-pin" class="mb-1 block text-xs font-medium">PIN</label>
          <input id="ueb-pin" v-model="pin" type="password" class="w-full rounded-control border border-border bg-surface px-3 py-2 text-sm" />
          <p class="mt-1 text-xs text-muted-foreground">PIN wird nicht gespeichert.</p>
        </div>
      </div>
    </TheCard>

    <!-- Schritt 3: Modus -->
    <TheCard v-if="aktuell === 3" id="ueb-step3" titel="Modus">
      <div id="ueb-modus" class="flex flex-wrap gap-3">
        <button
          id="ueb-modus-test"
          type="button"
          class="rounded-card border-2 px-6 py-4 text-left"
          :class="modus === 'test' ? 'border-primary bg-primary/5' : 'border-border'"
          @click="modus = 'test'"
        >
          <p class="font-semibold">Testfall</p>
          <p class="text-xs text-muted-foreground">Mit Testmerker, jederzeit erlaubt.</p>
        </button>
        <button
          id="ueb-modus-echt"
          type="button"
          class="rounded-card border-2 px-6 py-4 text-left"
          :class="modus === 'echt' ? 'border-danger bg-danger/5' : 'border-border'"
          @click="modus = 'echt'"
        >
          <p class="font-semibold text-danger">Echtfall</p>
          <p class="text-xs text-muted-foreground">Verbindliche Übermittlung ans Finanzamt.</p>
        </button>
      </div>
    </TheCard>

    <!-- Schritt 4: Bestätigung -->
    <TheCard v-if="aktuell === 4" id="ueb-step4" titel="Bestätigung">
      <div id="ueb-confirm" class="space-y-3 text-sm">
        <div class="flex flex-wrap gap-2">
          <BadgePill id="ueb-g-val" :tone="validierungOk ? 'success' : 'danger'" :label="validierungOk ? 'Validierung OK' : 'Validierung offen'" />
          <BadgePill id="ueb-g-cert" :tone="zertifikat ? 'success' : 'danger'" :label="zertifikat ? 'Zertifikat gewählt' : 'Zertifikat fehlt'" />
          <BadgePill id="ueb-g-hid" :tone="herstellerId ? 'success' : 'danger'" :label="herstellerId ? 'Hersteller-ID' : 'Hersteller-ID fehlt'" />
          <BadgePill id="ueb-g-modus" tone="info" :label="modus === 'echt' ? 'Modus: Echtfall' : 'Modus: Testfall'" />
        </div>
        <label id="ueb-freigabe" for="ueb-freigabe-check" class="flex items-center gap-2">
          <input id="ueb-freigabe-check" v-model="freigabeErteilt" type="checkbox" class="h-4 w-4 accent-primary" />
          <span>Freigabe erteilt (Freigeber-Rolle, Vier-Augen-Prinzip).</span>
        </label>
        <Banner v-if="modus === 'echt' && !kannEchtfall" id="ueb-guard" kind="warning">
          Echtfall gesperrt bis: Validierung OK, Zertifikat gewählt, Hersteller-ID hinterlegt und Freigabe erteilt.
        </Banner>
      </div>
    </TheCard>

    <!-- Navigation + Versand-CTAs -->
    <div id="ueb-nav" class="flex flex-wrap items-center justify-between gap-3">
      <TheButton id="ueb-back" variant="ghost" size="lg" :disabled="aktuell === 1 || gesendet" @click="zurueck">Zurück</TheButton>
      <div id="ueb-nav-right" class="flex flex-wrap gap-3">
        <TheButton v-if="aktuell < 4" id="ueb-next" variant="primary" size="lg" @click="weiter">Weiter</TheButton>
        <template v-else>
          <TheButton id="ueb-send-test" variant="outline" size="big" :disabled="gesendet" @click="senden('test')">Als Testfall senden</TheButton>
          <TheButton id="ueb-send-echt" variant="danger" size="big" :disabled="!kannEchtfall || gesendet" @click="senden('echt')">Echtfall übermitteln</TheButton>
        </template>
      </div>
    </div>
  </div>
</template>
