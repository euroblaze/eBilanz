<script setup lang="ts">
// Card — Basisflaeche (PRD §1.2). Optionaler Titel + Sub. KPI-Variante ueber Props.
withDefaults(
  defineProps<{ id?: string; titel?: string; sub?: string; padded?: boolean }>(),
  { padded: true },
)
</script>

<template>
  <section
    :id="id"
    class="bg-surface border border-border rounded-card shadow-card"
    :class="padded ? 'p-5' : ''"
  >
    <header v-if="titel || $slots.header" :id="id ? id + '-header' : undefined" class="mb-3">
      <slot name="header">
        <h3 class="text-sm font-semibold text-foreground">{{ titel }}</h3>
        <p v-if="sub" class="text-xs text-muted-foreground mt-0.5">{{ sub }}</p>
      </slot>
    </header>
    <slot />
  </section>
</template>
