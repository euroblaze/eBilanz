<script setup lang="ts">
import { computed } from 'vue'

// Banner (PRD §1.2) — persistente Info/Warnung/Fehler-Leiste.
type Kind = 'info' | 'warning' | 'error'
const props = withDefaults(defineProps<{ id?: string; kind?: Kind; titel?: string }>(), {
  kind: 'info',
})

const KIND_CLASSES: Record<Kind, string> = {
  info: 'bg-primary/10 border-primary/30 text-primary',
  warning: 'bg-warning/15 border-warning/40 text-[hsl(42_100%_30%)]',
  error: 'bg-danger/10 border-danger/40 text-danger',
}
const cls = computed(() => KIND_CLASSES[props.kind])
</script>

<template>
  <div :id="id" class="flex items-start gap-3 rounded-control border px-4 py-3 text-sm" :class="cls">
    <div :id="id ? id + '-body' : undefined" class="flex-1">
      <p v-if="titel" class="font-semibold">{{ titel }}</p>
      <div class="text-foreground/80"><slot /></div>
    </div>
    <div v-if="$slots.action" :id="id ? id + '-action' : undefined" class="shrink-0">
      <slot name="action" />
    </div>
  </div>
</template>
