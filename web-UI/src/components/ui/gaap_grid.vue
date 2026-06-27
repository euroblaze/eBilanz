<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ChevronDown, ChevronRight } from 'lucide-vue-next'
import { formatEur } from '@/libs/format'
import BadgePill from '@/components/ui/badge_pill.vue'

// GAAP-Tree-Grid (PRD §3.5) — hierarchische, editierbare Erfassungsmaske.
// Importwert (readonly) · Erfasster Wert (editierbar) · Δ · NIL-Toggle · Summen-Rollup.
export interface GaapNode {
  id: string
  label: string
  feldtyp?: 'Mussfeld' | 'Summenmussfeld' | 'rechnerisch notwendig' | 'Auffangposition'
  importwert?: number
  wertFinal?: number | null
  nil?: boolean
  children?: GaapNode[]
}

const props = defineProps<{ id?: string; nodes: GaapNode[] }>()

const collapsed = reactive(new Set<string>())
function toggle(id: string) {
  if (collapsed.has(id)) collapsed.delete(id)
  else collapsed.add(id)
}

function istBlatt(n: GaapNode): boolean {
  return !n.children?.length
}
// Summen-Rollup: Eltern = Summe der Kinder.
function importOf(n: GaapNode): number {
  if (n.children?.length) return n.children.reduce((a, c) => a + importOf(c), 0)
  return n.importwert ?? 0
}
function finalOf(n: GaapNode): number {
  if (n.children?.length) return n.children.reduce((a, c) => a + finalOf(c), 0)
  if (n.nil) return 0
  return n.wertFinal ?? n.importwert ?? 0
}
function diffOf(n: GaapNode): number {
  return finalOf(n) - importOf(n)
}

interface FlatRow {
  node: GaapNode
  depth: number
  expandable: boolean
  expanded: boolean
}
const rows = computed<FlatRow[]>(() => {
  const out: FlatRow[] = []
  const walk = (nodes: GaapNode[], depth: number) => {
    for (const n of nodes) {
      const hasChildren = !!n.children?.length
      const expanded = hasChildren && !collapsed.has(n.id)
      out.push({ node: n, depth, expandable: hasChildren, expanded })
      if (expanded) walk(n.children!, depth + 1)
    }
  }
  walk(props.nodes, 0)
  return out
})

const GRID = 'minmax(220px,1fr) 130px 140px 160px 120px 96px'
</script>

<template>
  <div :id="id" class="overflow-hidden rounded-card border border-border bg-surface shadow-card">
    <div :id="id ? id + '-scroll' : undefined" class="overflow-auto" style="max-height: 60vh">
      <!-- Kopf -->
      <div class="sticky top-0 z-10 grid items-center border-b border-border bg-muted/60 text-xs font-semibold" :style="{ gridTemplateColumns: GRID }">
        <div class="px-3 py-2">Taxonomie-Position</div>
        <div class="px-3 py-2">Typ</div>
        <div class="px-3 py-2 text-right">Importwert</div>
        <div class="px-3 py-2 text-right">Erfasster Wert</div>
        <div class="px-3 py-2 text-right">Δ</div>
        <div class="px-3 py-2 text-center">NIL</div>
      </div>

      <!-- Zeilen -->
      <div
        v-for="r in rows"
        :id="id ? id + '-row-' + r.node.id : undefined"
        :key="r.node.id"
        class="grid items-center border-b border-border text-sm hover:bg-accent/30"
        :style="{ gridTemplateColumns: GRID }"
      >
        <!-- Position -->
        <div class="flex items-center gap-1 px-3 py-1.5" :style="{ paddingLeft: r.depth * 16 + 12 + 'px' }">
          <button v-if="r.expandable" type="button" class="shrink-0 text-muted-foreground hover:text-primary" @click="toggle(r.node.id)">
            <ChevronDown v-if="r.expanded" class="h-4 w-4" />
            <ChevronRight v-else class="h-4 w-4" />
          </button>
          <span v-else class="w-4 shrink-0" />
          <span v-if="r.node.feldtyp === 'Mussfeld'" class="mr-1 h-1.5 w-1.5 shrink-0 rounded-pill bg-danger" title="Mussfeld" />
          <span class="truncate" :class="r.expandable ? 'font-semibold text-foreground' : ''">{{ r.node.label }}</span>
        </div>

        <!-- Typ -->
        <div class="px-3 py-1.5">
          <BadgePill v-if="r.node.feldtyp" :tone="r.node.feldtyp === 'Summenmussfeld' ? 'warning' : r.node.feldtyp === 'Mussfeld' ? 'danger' : 'muted'" :label="r.node.feldtyp" />
        </div>

        <!-- Importwert (readonly, gerundet) -->
        <div class="px-3 py-1.5 text-right text-muted-foreground">{{ formatEur(importOf(r.node)) }}</div>

        <!-- Erfasster Wert -->
        <div class="px-3 py-1.5 text-right">
          <template v-if="istBlatt(r.node)">
            <span v-if="r.node.nil" class="text-muted-foreground italic">NIL</span>
            <input
              v-else
              :id="id ? id + '-inp-' + r.node.id : undefined"
              v-model.number="r.node.wertFinal"
              type="number"
              step="0.01"
              :placeholder="String(r.node.importwert ?? 0)"
              class="w-full rounded-control border border-border bg-surface px-2 py-1 text-right text-sm"
            />
          </template>
          <span v-else class="font-semibold">{{ formatEur(finalOf(r.node)) }}</span>
        </div>

        <!-- Δ -->
        <div class="px-3 py-1.5 text-right" :class="Math.abs(diffOf(r.node)) > 0.005 ? 'text-warning font-medium' : 'text-muted-foreground'">
          {{ formatEur(diffOf(r.node)) }}
        </div>

        <!-- NIL-Toggle (nur Mussfeld-Blätter) -->
        <div class="px-3 py-1.5 text-center">
          <input
            v-if="istBlatt(r.node) && r.node.feldtyp === 'Mussfeld'"
            :id="id ? id + '-nil-' + r.node.id : undefined"
            v-model="r.node.nil"
            type="checkbox"
            class="h-4 w-4 accent-primary"
            title="kein Sachverhalt (NIL)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
