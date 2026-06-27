<script setup lang="ts">
// Big-Prompt (PRD §1.2 / §6) — Hero-CTA & Empty-State mit grosser Schaltflaeche.
defineProps<{ id?: string; titel: string; text?: string }>()
</script>

<template>
  <div
    :id="id"
    class="rounded-card border border-primary/20 bg-gradient-to-br from-primary/5 to-surface p-6 shadow-card"
  >
    <div :id="id ? id + '-content' : undefined" class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div :id="id ? id + '-texts' : undefined">
        <h2 class="text-lg font-bold text-foreground">{{ titel }}</h2>
        <p v-if="text" class="mt-1 text-sm text-muted-foreground">{{ text }}</p>
      </div>
      <div :id="id ? id + '-cta' : undefined" class="shrink-0">
        <slot name="cta" />
      </div>
    </div>
  </div>
</template>
