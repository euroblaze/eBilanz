<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ChevronRight, ChevronDown, Lock } from 'lucide-vue-next'
import BadgePill from '@/components/ui/badge_pill.vue'

// Taxonomie-Baum (PRD §3.4) — suchbar, mit Feldtyp-Badge je Position.
// Flache Darstellung mit Einrueckung (kein rekursives Component -> robust + einfach).
export type Feldtyp =
  | 'Mussfeld'
  | 'Summenmussfeld'
  | 'Kontennachweis erwünscht'
  | 'rechnerisch notwendig'
  | 'Auffangposition'

export interface TaxNode {
  id: string
  label: string
  feldtyp?: Feldtyp
  children?: TaxNode[]
}

const props = withDefaults(
  defineProps<{ id?: string; nodes: TaxNode[]; search?: string }>(),
  { search: '' },
)
const emit = defineEmits<{ select: [node: TaxNode] }>()

// Feldtyp -> Badge-Ton (Zwei-Ton-Palette)
type Tone = 'muted' | 'info' | 'primary' | 'success' | 'warning' | 'danger'
const FELDTYP_TONE: Record<Feldtyp, Tone> = {
  Mussfeld: 'danger',
  Summenmussfeld: 'warning',
  'Kontennachweis erwünscht': 'info',
  'rechnerisch notwendig': 'muted',
  Auffangposition: 'primary',
}

// Eingeklappte Knoten (Standard: alles ausgeklappt)
const collapsed = reactive(new Set<string>())
function toggle(id: string) {
  if (collapsed.has(id)) collapsed.delete(id)
  else collapsed.add(id)
}

// Summenmussfeld / Knoten mit Kindern sind nicht direkt zuweisbar (PRD-Regel §3.4).
function blockiert(n: TaxNode): boolean {
  return n.feldtyp === 'Summenmussfeld' || !!n.children?.length
}

function descendantMatch(n: TaxNode, q: string): boolean {
  if (!n.children?.length) return false
  return n.children.some((c) => c.label.toLowerCase().includes(q) || descendantMatch(c, q))
}

interface FlatRow {
  node: TaxNode
  depth: number
  expandable: boolean
  expanded: boolean
}

// Sichtbare Zeilen berechnen (Suche erzwingt Aufklappen passender Aeste).
const rows = computed<FlatRow[]>(() => {
  const q = props.search.trim().toLowerCase()
  const out: FlatRow[] = []
  const walk = (nodes: TaxNode[], depth: number) => {
    for (const n of nodes) {
      const hasChildren = !!n.children?.length
      if (q) {
        const selfMatch = n.label.toLowerCase().includes(q)
        const descMatch = descendantMatch(n, q)
        if (!selfMatch && !descMatch) continue
        out.push({ node: n, depth, expandable: hasChildren, expanded: true })
        if (hasChildren) walk(n.children!, depth + 1)
      } else {
        const expanded = hasChildren && !collapsed.has(n.id)
        out.push({ node: n, depth, expandable: hasChildren, expanded })
        if (expanded) walk(n.children!, depth + 1)
      }
    }
  }
  walk(props.nodes, 0)
  return out
})
</script>

<template>
  <ul :id="id" class="space-y-0.5">
    <li v-for="r in rows" :id="id ? id + '-node-' + r.node.id : undefined" :key="r.node.id">
      <div
        class="flex items-center gap-2 rounded-control px-2 py-1.5 text-sm hover:bg-accent"
        :class="blockiert(r.node) ? 'text-muted-foreground' : 'cursor-pointer'"
        :style="{ paddingLeft: r.depth * 16 + 8 + 'px' }"
        @click="!blockiert(r.node) && emit('select', r.node)"
      >
        <!-- Aufklapp-Chevron -->
        <button
          v-if="r.expandable"
          :id="id ? id + '-toggle-' + r.node.id : undefined"
          type="button"
          class="shrink-0 text-muted-foreground hover:text-primary"
          @click.stop="toggle(r.node.id)"
        >
          <ChevronDown v-if="r.expanded" class="h-4 w-4" />
          <ChevronRight v-else class="h-4 w-4" />
        </button>
        <span v-else class="w-4 shrink-0" />

        <span class="flex-1 truncate" :class="r.expandable ? 'font-medium text-foreground' : ''">
          {{ r.node.label }}
        </span>

        <Lock v-if="blockiert(r.node) && r.node.feldtyp === 'Summenmussfeld'" class="h-3.5 w-3.5 shrink-0 text-warning" />
        <BadgePill
          v-if="r.node.feldtyp"
          :id="id ? id + '-typ-' + r.node.id : undefined"
          :tone="FELDTYP_TONE[r.node.feldtyp]"
          :label="r.node.feldtyp"
        />
      </div>
    </li>
  </ul>
</template>
