<script setup lang="ts">
import { computed } from 'vue'

// Button — Varianten/Groessen aus PRD §1.2 + simplify Button.tsx (Hover-Lift, Shadow).
// danger = Rot #EA5562 (reserviert fuer destruktive Aktionen / Echtfall, PRD §5).
type Variant = 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost'
type Size = 'md' | 'lg' | 'big' // big = Hero-CTA >= 56px (PRD Big-Prompt)

const props = withDefaults(
  defineProps<{ variant?: Variant; size?: Size; id?: string; disabled?: boolean }>(),
  { variant: 'primary', size: 'md', disabled: false },
)

const base =
  'inline-flex items-center justify-center gap-2 font-semibold rounded-control ' +
  'transition-all duration-300 ease-out transform hover:-translate-y-0.5 active:scale-[.98] ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ' +
  'disabled:opacity-50 disabled:pointer-events-none'

const variants: Record<Variant, string> = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary-700 shadow-card hover:shadow-pop',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary-700 shadow-card',
  danger: 'bg-danger text-white hover:bg-secondary-700 shadow-card hover:shadow-pop',
  outline: 'border-2 border-border text-foreground hover:border-primary hover:text-primary',
  ghost: 'text-muted-foreground hover:text-primary hover:bg-accent',
}

const sizes: Record<Size, string> = {
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
  big: 'px-8 text-lg min-h-[56px]', // Hero-CTA
}

const classes = computed(() => [base, variants[props.variant], sizes[props.size]])
</script>

<template>
  <button :id="id" type="button" :disabled="disabled" :class="classes">
    <slot />
  </button>
</template>
