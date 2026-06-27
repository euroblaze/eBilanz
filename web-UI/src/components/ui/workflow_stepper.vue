<script setup lang="ts">
// Workflow-Stepper (PRD §3.1) — horizontaler 6-Schritt-Fortschritt.
export interface Step {
  nr: number
  label: string
  state: 'done' | 'current' | 'todo'
}
defineProps<{ id?: string; steps: Step[] }>()

function dotClass(state: Step['state']): string {
  if (state === 'done') return 'bg-primary text-white border-primary'
  if (state === 'current') return 'bg-surface text-primary border-primary ring-2 ring-primary/30'
  return 'bg-surface text-muted-foreground border-border'
}
</script>

<template>
  <ol :id="id" class="flex items-center gap-2 overflow-x-auto">
    <li
      v-for="(s, i) in steps"
      :key="s.nr"
      :id="id ? id + '-step-' + s.nr : undefined"
      class="flex min-w-fit items-center gap-2"
    >
      <span
        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-pill border text-xs font-bold"
        :class="dotClass(s.state)"
      >{{ s.nr }}</span>
      <span
        class="whitespace-nowrap text-xs"
        :class="s.state === 'todo' ? 'text-muted-foreground' : 'text-foreground font-medium'"
      >{{ s.label }}</span>
      <span
        v-if="i < steps.length - 1"
        :id="id ? id + '-sep-' + s.nr : undefined"
        class="mx-1 h-px w-6 bg-border"
        aria-hidden="true"
      />
    </li>
  </ol>
</template>
