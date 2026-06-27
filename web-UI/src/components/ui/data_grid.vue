<script setup lang="ts" generic="T extends Record<string, unknown>">
import { computed, ref } from 'vue'
import {
  useVueTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/vue-table'
import { useVirtualizer } from '@tanstack/vue-virtual'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-vue-next'

// DataGrid (PRD §1.2) — TanStack Table (Datenmodell) + TanStack Virtual (virtuelles Scrollen).
// Markup ist eigenes (CSS-Grid) -> volle Token-Treue. Features: Sortierung, Spalten-Filter,
// Sticky-Header, virtuelles Scrollen, Summen-Footer, benannte Zell-Slots (cell-<field>).
export interface GridColumn {
  field: string
  header: string
  width?: number // px; fehlt -> flexibel (1fr)
  align?: 'left' | 'right'
  sortable?: boolean
  filter?: boolean
  format?: (value: unknown) => string
  footer?: 'sum' // Summe ueber gefilterte Zeilen
  mono?: boolean
}

const props = withDefaults(
  defineProps<{
    id?: string
    columns: GridColumn[]
    data: T[]
    rowKey?: string
    rowHeight?: number
    maxHeight?: string
    // optionaler linker Akzent je Zeile (z. B. Diff-Status) -> Tailwind-Klasse oder undefined
    rowAccent?: (row: T) => string | undefined
  }>(),
  { rowKey: 'id', rowHeight: 44, maxHeight: '520px' },
)

const sorting = ref<SortingState>([])
const columnFilters = ref<ColumnFiltersState>([])
const filterRowVisible = ref(false)

// Minimale TanStack-Spaltendefinition nur fuer Sortier-/Filterlogik.
const tanstackColumns = computed<ColumnDef<T>[]>(() =>
  props.columns.map((c) => ({
    accessorKey: c.field,
    header: c.header,
    enableSorting: c.sortable ?? false,
    enableColumnFilter: c.filter ?? false,
    filterFn: 'includesString', // case-insensitive Teilstring
  })),
)

const table = useVueTable({
  get data() {
    return props.data
  },
  get columns() {
    return tanstackColumns.value
  },
  state: {
    get sorting() {
      return sorting.value
    },
    get columnFilters() {
      return columnFilters.value
    },
  },
  onSortingChange: (u) => {
    sorting.value = typeof u === 'function' ? u(sorting.value) : u
  },
  onColumnFiltersChange: (u) => {
    columnFilters.value = typeof u === 'function' ? u(columnFilters.value) : u
  },
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
})

const rows = computed(() => table.getRowModel().rows)

// CSS-Grid-Spalten: feste px-Breiten, sonst flexibel.
const gridTemplate = computed(() =>
  props.columns.map((c) => (c.width ? `${c.width}px` : 'minmax(120px, 1fr)')).join(' '),
)

// Virtuelles Scrollen
const scrollEl = ref<HTMLElement | null>(null)
const virtualizer = useVirtualizer(
  computed(() => ({
    count: rows.value.length,
    getScrollElement: () => scrollEl.value,
    estimateSize: () => props.rowHeight,
    overscan: 12,
  })),
)
const virtualRows = computed(() => virtualizer.value.getVirtualItems())
const totalSize = computed(() => virtualizer.value.getTotalSize())

// Sortierung umschalten
function toggleSort(col: GridColumn) {
  if (!col.sortable) return
  table.getColumn(col.field)?.toggleSorting()
}
function sortDir(field: string): 'asc' | 'desc' | false {
  const s = sorting.value.find((x) => x.id === field)
  return s ? (s.desc ? 'desc' : 'asc') : false
}

// Spalten-Filter
function setFilter(field: string, value: string) {
  table.getColumn(field)?.setFilterValue(value || undefined)
}
function filterValue(field: string): string {
  return (table.getColumn(field)?.getFilterValue() as string) ?? ''
}

// Summen-Footer (ueber gefilterte Zeilen)
const hasFooter = computed(() => props.columns.some((c) => c.footer === 'sum'))
function footerValue(col: GridColumn): string {
  if (col.footer !== 'sum') return ''
  const sum = table
    .getFilteredRowModel()
    .rows.reduce((acc, r) => acc + Number(r.getValue(col.field) ?? 0), 0)
  return col.format ? col.format(sum) : String(sum)
}

function display(col: GridColumn, value: unknown): string {
  return col.format ? col.format(value) : value == null ? '' : String(value)
}

defineExpose({ filterRowVisible })
</script>

<template>
  <div :id="id" class="overflow-hidden rounded-card border border-border bg-surface shadow-card">
    <!-- Toolbar -->
    <div :id="id ? id + '-toolbar' : undefined" class="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
      <span :id="id ? id + '-count' : undefined" class="text-xs text-muted-foreground">
        {{ rows.length }} Zeilen
      </span>
      <button
        :id="id ? id + '-filter-toggle' : undefined"
        type="button"
        class="rounded-control px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-primary"
        @click="filterRowVisible = !filterRowVisible"
      >
        Spalten-Filter {{ filterRowVisible ? 'ausblenden' : 'anzeigen' }}
      </button>
    </div>

    <!-- Scroll-Container (Scroll-Element fuer Virtualizer) -->
    <div
      :id="id ? id + '-scroll' : undefined"
      ref="scrollEl"
      class="relative overflow-auto"
      :style="{ maxHeight: maxHeight }"
    >
      <!-- Sticky Kopf + Filterzeile -->
      <div :id="id ? id + '-head' : undefined" class="sticky top-0 z-20 bg-surface">
        <div
          class="grid items-center border-b border-border bg-muted/60 text-xs font-semibold text-foreground"
          :style="{ gridTemplateColumns: gridTemplate }"
        >
          <div
            v-for="col in columns"
            :id="id ? id + '-col-' + col.field : undefined"
            :key="col.field"
            class="flex items-center gap-1 px-3 py-2 select-none"
            :class="[col.align === 'right' ? 'justify-end' : '', col.sortable ? 'cursor-pointer hover:text-primary' : '']"
            @click="toggleSort(col)"
          >
            <span>{{ col.header }}</span>
            <template v-if="col.sortable">
              <ChevronUp v-if="sortDir(col.field) === 'asc'" class="h-3.5 w-3.5 text-primary" />
              <ChevronDown v-else-if="sortDir(col.field) === 'desc'" class="h-3.5 w-3.5 text-primary" />
              <ChevronsUpDown v-else class="h-3.5 w-3.5 text-muted-foreground/50" />
            </template>
          </div>
        </div>
        <!-- Filterzeile -->
        <div
          v-if="filterRowVisible"
          class="grid border-b border-border bg-surface"
          :style="{ gridTemplateColumns: gridTemplate }"
        >
          <div v-for="col in columns" :key="col.field" class="px-2 py-1.5">
            <input
              v-if="col.filter"
              :id="id ? id + '-flt-' + col.field : undefined"
              :value="filterValue(col.field)"
              type="text"
              placeholder="Filtern…"
              class="w-full rounded-control border border-border bg-surface px-2 py-1 text-xs"
              @input="setFilter(col.field, ($event.target as HTMLInputElement).value)"
            />
          </div>
        </div>
      </div>

      <!-- Virtualisierter Body -->
      <div
        :id="id ? id + '-body' : undefined"
        class="relative"
        :style="{ height: totalSize + 'px' }"
      >
        <div
          v-for="vr in virtualRows"
          :id="id ? id + '-row-' + (rows[vr.index].original as Record<string, unknown>)[rowKey] : undefined"
          :key="(rows[vr.index].original as Record<string, unknown>)[rowKey] as string"
          class="absolute left-0 top-0 grid w-full items-center border-b border-border text-sm hover:bg-accent/40"
          :class="rowAccent ? rowAccent(rows[vr.index].original) : ''"
          :style="{ height: rowHeight + 'px', transform: 'translateY(' + vr.start + 'px)', gridTemplateColumns: gridTemplate }"
        >
          <div
            v-for="col in columns"
            :key="col.field"
            class="truncate px-3"
            :class="[col.align === 'right' ? 'text-right' : '', col.mono ? 'font-mono text-xs' : '']"
          >
            <slot
              :name="'cell-' + col.field"
              :row="rows[vr.index].original"
              :value="rows[vr.index].getValue(col.field)"
            >
              {{ display(col, rows[vr.index].getValue(col.field)) }}
            </slot>
          </div>
        </div>
      </div>

      <!-- Leerzustand -->
      <div v-if="rows.length === 0" :id="id ? id + '-empty' : undefined" class="px-3 py-10 text-center text-sm text-muted-foreground">
        Keine Daten.
      </div>

      <!-- Sticky Summen-Footer -->
      <div
        v-if="hasFooter"
        :id="id ? id + '-foot' : undefined"
        class="sticky bottom-0 z-20 grid border-t border-border bg-muted/80 text-sm font-semibold"
        :style="{ gridTemplateColumns: gridTemplate }"
      >
        <div
          v-for="col in columns"
          :key="col.field"
          class="truncate px-3 py-2"
          :class="[col.align === 'right' ? 'text-right' : '', col.mono ? 'font-mono text-xs' : '']"
        >
          {{ footerValue(col) }}
        </div>
      </div>
    </div>
  </div>
</template>
