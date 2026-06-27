<script setup lang="ts">
import { X } from 'lucide-vue-next'

// Drawer (PRD §1.2) — rechtes Detail-/Edit-Panel mit Overlay.
defineProps<{ id?: string; modelValue: boolean; titel?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()
function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="modelValue" :id="id" class="fixed inset-0 z-50 flex">
        <div :id="id ? id + '-overlay' : undefined" class="flex-1 bg-black/30" @click="close" />
        <aside
          :id="id ? id + '-panel' : undefined"
          class="h-full w-full max-w-md overflow-auto bg-surface shadow-pop"
        >
          <header
            :id="id ? id + '-head' : undefined"
            class="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface px-4 py-3"
          >
            <h3 class="text-sm font-semibold text-foreground">{{ titel }}</h3>
            <button :id="id ? id + '-close' : undefined" type="button" class="rounded-control p-1 hover:bg-accent" @click="close">
              <X class="h-5 w-5 text-muted-foreground" />
            </button>
          </header>
          <div :id="id ? id + '-body' : undefined" class="p-4">
            <slot />
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
</style>
