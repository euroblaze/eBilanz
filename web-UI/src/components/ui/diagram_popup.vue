<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { X, Plus, Minus, RotateCcw, Move } from 'lucide-vue-next'

// Diagramm-Popup — verschiebbares Fenster mit zoom-/schwenkbarem Bild (SVG).
// Zero-Dep: CSS-Transform (translate + scale), Pointer-Events.
const props = withDefaults(
  defineProps<{ id?: string; modelValue: boolean; src: string; titel?: string }>(),
  { titel: 'Datenfluss', id: 'diagram' },
)
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

function close() {
  emit('update:modelValue', false)
}

// --- Fensterposition (verschiebbar via Titelleiste) -------------------------
// Fenster = 95% der Fenstergroesse, zentriert.
const win = ref({ x: 0, y: 0 })
function center() {
  win.value = {
    x: Math.round(window.innerWidth * 0.025),
    y: Math.round(window.innerHeight * 0.025),
  }
}
let winDrag: { sx: number; sy: number; ox: number; oy: number } | null = null
function onWinDown(e: PointerEvent) {
  winDrag = { sx: e.clientX, sy: e.clientY, ox: win.value.x, oy: win.value.y }
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
}
function onWinMove(e: PointerEvent) {
  if (!winDrag) return
  win.value = { x: winDrag.ox + (e.clientX - winDrag.sx), y: winDrag.oy + (e.clientY - winDrag.sy) }
}
function onWinUp() {
  winDrag = null
}

// --- Zoom + Pan (Bildinhalt) ------------------------------------------------
const zoom = ref(1)
const pan = ref({ x: 0, y: 0 })
const MIN = 0.2
const MAX = 6
let panDrag: { sx: number; sy: number; ox: number; oy: number } | null = null

function clampZoom(z: number) {
  return Math.min(MAX, Math.max(MIN, z))
}
function onWheel(e: WheelEvent) {
  // Cursor-verankertes Zoomen relativ zur Canvas-Mitte.
  const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const cx = e.clientX - rect.left - rect.width / 2
  const cy = e.clientY - rect.top - rect.height / 2
  const newZoom = clampZoom(zoom.value * factor)
  const ratio = newZoom / zoom.value
  pan.value = { x: cx - (cx - pan.value.x) * ratio, y: cy - (cy - pan.value.y) * ratio }
  zoom.value = newZoom
}
function onPanDown(e: PointerEvent) {
  panDrag = { sx: e.clientX, sy: e.clientY, ox: pan.value.x, oy: pan.value.y }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}
function onPanMove(e: PointerEvent) {
  if (!panDrag) return
  pan.value = { x: panDrag.ox + (e.clientX - panDrag.sx), y: panDrag.oy + (e.clientY - panDrag.sy) }
}
function onPanUp() {
  panDrag = null
}
function zoomIn() {
  zoom.value = clampZoom(zoom.value * 1.2)
}
function zoomOut() {
  zoom.value = clampZoom(zoom.value / 1.2)
}
function reset() {
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
}

// ESC schliesst; beim Öffnen zuruecksetzen.
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      reset()
      center()
      window.addEventListener('keydown', onKey)
    } else {
      window.removeEventListener('keydown', onKey)
    }
  },
)
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      :id="id"
      class="fixed z-50 flex h-[95vh] w-[95vw] flex-col overflow-hidden rounded-card border border-border bg-surface shadow-pop"
      :style="{ left: win.x + 'px', top: win.y + 'px' }"
    >
      <!-- Titelleiste (verschiebbar) -->
      <header
        :id="id + '-titlebar'"
        class="flex cursor-move select-none items-center gap-2 border-b border-border bg-muted/60 px-3 py-2"
        @pointerdown="onWinDown"
        @pointermove="onWinMove"
        @pointerup="onWinUp"
      >
        <Move class="h-4 w-4 text-muted-foreground" />
        <span :id="id + '-title'" class="flex-1 text-sm font-semibold text-foreground">{{ titel }}</span>
        <button :id="id + '-zoom-out'" type="button" class="rounded-control p-1 hover:bg-accent" title="Verkleinern" @click="zoomOut">
          <Minus class="h-4 w-4" />
        </button>
        <span :id="id + '-zoom-label'" class="w-12 text-center text-xs text-muted-foreground">{{ Math.round(zoom * 100) }}%</span>
        <button :id="id + '-zoom-in'" type="button" class="rounded-control p-1 hover:bg-accent" title="Vergrößern" @click="zoomIn">
          <Plus class="h-4 w-4" />
        </button>
        <button :id="id + '-reset'" type="button" class="rounded-control p-1 hover:bg-accent" title="Zurücksetzen" @click="reset">
          <RotateCcw class="h-4 w-4" />
        </button>
        <button :id="id + '-close'" type="button" class="rounded-control p-1 hover:bg-accent" title="Schließen" @click="close">
          <X class="h-5 w-5 text-muted-foreground" />
        </button>
      </header>

      <!-- Canvas (zoom-/schwenkbar) -->
      <div
        :id="id + '-canvas'"
        class="relative min-h-0 flex-1 cursor-grab touch-none overflow-hidden bg-[hsl(var(--muted))] active:cursor-grabbing"
        @wheel.prevent="onWheel"
        @pointerdown="onPanDown"
        @pointermove="onPanMove"
        @pointerup="onPanUp"
        @pointerleave="onPanUp"
      >
        <img
          :id="id + '-img'"
          :src="src"
          alt="E-Bilanz Datenfluss"
          draggable="false"
          class="absolute left-1/2 top-1/2 max-w-none select-none"
          :style="{
            transform: `translate(-50%, -50%) translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }"
        />
      </div>

      <!-- Fusszeile / Hinweis -->
      <footer :id="id + '-hint'" class="border-t border-border px-3 py-1.5 text-xs text-muted-foreground">
        Mausrad = Zoom · Ziehen = Verschieben · Titelleiste ziehen = Fenster bewegen · ESC = Schließen
      </footer>
    </div>
  </Teleport>
</template>
