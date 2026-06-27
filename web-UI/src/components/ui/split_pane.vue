<script setup lang="ts">
// Split-Pane (PRD §1.2 / §3.4) — zwei Spalten nebeneinander (links/rechts).
// Stapelt auf < lg zu einer Spalte. Inhalt je Pane via Slots #left / #right.
defineProps<{ id?: string }>()
</script>

<template>
  <div :id="id" class="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
    <div :id="id ? id + '-left' : undefined" class="min-w-0">
      <slot name="left" />
    </div>
    <div :id="id ? id + '-right' : undefined" class="min-w-0">
      <slot name="right" />
    </div>
  </div>
</template>
