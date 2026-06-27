<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Grid2x2, Building2, Upload, GitMerge, Table2, List, CheckCircle2, Send, History,
  HelpCircle, ChevronLeft, Menu, CircleDot,
} from 'lucide-vue-next'
import { useWjStore } from '@/stores/wj_store'
import BadgePill from '@/components/ui/badge_pill.vue'
import TheButton from '@/components/ui/the_button.vue'
import DiagramPopup from '@/components/ui/diagram_popup.vue'

// App-Shell (PRD §2): sticky Topbar (64px) + einklappbare Sidebar (260px).
const wj = useWjStore()
const route = useRoute()
const collapsed = ref(false) // Sidebar einklappen (PRD §8: < 1280px)
const diagramOpen = ref(false) // Datenfluss-Diagramm-Popup (Hilfe-Icon)

// Hauptmenue (PRD §2.2). fortschritt: leer | teil | voll (Punkt-Indikator).
// Stammdaten ist auf den letzten Menuepunkt verschoben (Wunsch).
const nav = [
  { icon: Grid2x2, label: 'Übersicht', route: '/dashboard', fortschritt: 'voll' },
  { icon: Upload, label: 'Saldenimport', route: '/import', fortschritt: 'leer' },
  { icon: GitMerge, label: 'Konten-Mapping', route: '/mapping', fortschritt: 'leer', badge: 'offen: 36' },
  { icon: Table2, label: 'E-Bilanz Erfassung', route: '/gaap', fortschritt: 'leer' },
  { icon: List, label: 'Kontennachweise', route: '/kontennachweise', fortschritt: 'leer' },
  { icon: CheckCircle2, label: 'Validierung', route: '/validierung', fortschritt: 'leer', badge: '0' },
  { icon: Send, label: 'Übermittlung', route: '/uebermittlung', fortschritt: 'leer' },
  { icon: History, label: 'Protokoll & Historie', route: '/protokoll', fortschritt: 'leer' },
  { icon: Building2, label: 'Stammdaten (GCD)', route: '/stammdaten', fortschritt: 'teil' },
]

function fortschrittClass(f: string): string {
  if (f === 'voll') return 'fill-primary text-primary'
  if (f === 'teil') return 'fill-warning text-warning'
  return 'fill-transparent text-border'
}
</script>

<template>
  <div id="app-shell" class="min-h-screen bg-background">
    <!-- Topbar (PRD §2.1) -->
    <header
      id="topbar"
      class="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-surface px-4"
    >
      <button id="topbar-sidebar-toggle" type="button" class="rounded-control p-2 hover:bg-accent" @click="collapsed = !collapsed">
        <Menu class="h-5 w-5 text-muted-foreground" />
      </button>
      <router-link id="topbar-logo" to="/dashboard" class="flex items-center gap-2 font-bold text-primary">
        <span class="rounded-control bg-primary px-2 py-1 text-sm text-white">E-Bilanz</span>
        <span class="hidden text-sm text-muted-foreground sm:inline">simplify-erp.de</span>
      </router-link>

      <!-- WJ-Selector (zentrales Arbeitsobjekt) -->
      <div id="topbar-wj-selector" class="ml-2">
        <select
          id="topbar-wj-select"
          :value="wj.aktivesProjektId"
          class="rounded-control border border-border bg-surface px-3 py-1.5 text-sm font-medium"
          @change="wj.setAktivesProjekt(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="p in wj.projekte" :id="'wj-opt-' + p.id" :key="p.id" :value="p.id">
            {{ p.bezeichnung }}
          </option>
        </select>
      </div>

      <!-- Seitentitel (aus Route-Meta) — zwischen WJ-Selector und Taxonomie-Badge -->
      <h1 id="page-title" class="ml-2 truncate text-base font-bold text-foreground">
        {{ (route.meta.titel as string) ?? '' }}
      </h1>

      <div id="topbar-spacer" class="flex-1" />

      <!-- Status-Pills (PRD §2.1) -->
      <BadgePill id="topbar-taxonomie" tone="info" :label="wj.aktivesProjekt.taxonomieLabel" />
      <BadgePill
        id="topbar-eric"
        :tone="wj.ericAktiv ? 'success' : 'danger'"
        :label="wj.ericAktiv ? 'ERiC ' + wj.ericVersion + ' aktiv' : 'ERiC Update nötig'"
      />
      <span id="topbar-odoo" class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span class="h-2.5 w-2.5 rounded-pill" :class="wj.odooVerbunden ? 'bg-primary' : 'bg-danger'" />
        Odoo{{ wj.odooDb ? ' / ' + wj.odooDb : '' }}
      </span>
      <button id="topbar-help" type="button" title="Datenfluss-Diagramm" class="rounded-control p-2 hover:bg-accent" @click="diagramOpen = true">
        <HelpCircle class="h-5 w-5 text-muted-foreground" />
      </button>
      <div id="topbar-avatar" class="h-8 w-8 rounded-pill bg-primary-700 text-center text-sm font-bold leading-8 text-white">
        SB
      </div>
    </header>

    <div id="shell-body" class="flex">
      <!-- Sidebar (PRD §2.2) -->
      <aside
        id="sidebar"
        class="sticky top-16 hidden h-[calc(100vh-4rem)] shrink-0 flex-col border-r border-border bg-surface transition-all md:flex"
        :class="collapsed ? 'w-16' : 'w-[260px]'"
      >
        <nav id="sidebar-nav" class="flex-1 overflow-y-auto p-2">
          <router-link
            v-for="item in nav"
            :id="'nav-' + item.route.replace('/', '')"
            :key="item.route"
            :to="item.route"
            class="group mb-0.5 flex items-center gap-3 rounded-control px-3 py-2 text-sm hover:bg-accent"
            :class="route.path.startsWith(item.route) ? 'bg-accent font-semibold text-primary' : 'text-foreground'"
          >
            <component :is="item.icon" class="h-5 w-5 shrink-0" />
            <span v-if="!collapsed" class="flex-1 truncate">{{ item.label }}</span>
            <BadgePill v-if="!collapsed && item.badge" tone="muted" :label="item.badge" />
            <CircleDot v-if="!collapsed" class="h-3 w-3 shrink-0" :class="fortschrittClass(item.fortschritt)" />
          </router-link>
        </nav>

        <!-- Fixierte Aktionen unten (PRD §2.2) -->
        <div v-if="!collapsed" id="sidebar-actions" class="space-y-2 border-t border-border p-3">
          <TheButton id="sidebar-validate" variant="outline" size="lg" class="w-full">Jetzt validieren</TheButton>
          <TheButton id="sidebar-submit" variant="primary" size="lg" class="w-full" @click="wj.laden()">Sync mit Odoo</TheButton>
        </div>
        <button
          v-else
          id="sidebar-expand"
          type="button"
          class="border-t border-border p-3 text-muted-foreground hover:text-primary"
          @click="collapsed = false"
        >
          <ChevronLeft class="h-5 w-5 rotate-180" />
        </button>
      </aside>

      <!-- Inhalt -->
      <main id="main-content" class="min-w-0 flex-1 p-4 md:p-6">
        <router-view />
      </main>
    </div>

    <!-- Datenfluss-Diagramm (Hilfe-Icon) -->
    <DiagramPopup id="datenfluss" v-model="diagramOpen" src="/ebilanz-datenfluss.svg" titel="E-Bilanz Datenfluss" />
  </div>
</template>
