<script setup lang="ts">
import { computed } from 'vue'

// Badge/Pill (PRD §1.2 + §1.3). Zwei-Ton: success/info = Blau, unterschieden ueber Fuellung.
// Entweder `status` (mappt auf §1.3) oder `tone` direkt setzen.
type Tone = 'muted' | 'info' | 'primary' | 'success' | 'warning' | 'danger'

const props = defineProps<{ id?: string; status?: string; tone?: Tone; label?: string }>()

// §1.3 Statuswerte → Ton (Fuellung: solid vs. soft via Ton-Klassen unten)
const STATUS_MAP: Record<string, Tone> = {
  Entwurf: 'muted',
  'In Bearbeitung': 'info',
  Geprüft: 'primary',
  'Validiert OK': 'success',
  'Validierung Fehler': 'danger',
  'Testfall gesendet': 'info',
  'Echtfall gesendet': 'success',
  Abgelehnt: 'danger',
  Berichtigung: 'warning',
}

const effectiveTone = computed<Tone>(
  () => props.tone ?? (props.status ? STATUS_MAP[props.status] ?? 'muted' : 'muted'),
)

// solid = kraeftige Fuellung (success/danger/warning), soft = getoent (info/muted),
// primary = dunkles Blau (Geprueft) zur Abgrenzung von success.
const TONE_CLASSES: Record<Tone, string> = {
  muted: 'bg-muted text-muted-foreground',
  info: 'bg-primary/10 text-primary',
  primary: 'bg-primary-700 text-white',
  success: 'bg-primary text-white',
  warning: 'bg-warning text-black',
  danger: 'bg-danger text-white',
}

const text = computed(() => props.label ?? props.status ?? '')
</script>

<template>
  <span
    :id="id"
    class="inline-flex items-center rounded-pill px-2.5 py-0.5 text-xs font-medium whitespace-nowrap"
    :class="TONE_CLASSES[effectiveTone]"
  >
    <slot>{{ text }}</slot>
  </span>
</template>
