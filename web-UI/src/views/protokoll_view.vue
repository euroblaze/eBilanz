<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { formatDateTime } from '@/libs/format'
import { api, ApiError } from '@/libs/api'
import TheButton from '@/components/ui/the_button.vue'
import BadgePill from '@/components/ui/badge_pill.vue'
import Banner from '@/components/ui/banner.vue'
import DataGrid, { type GridColumn } from '@/components/ui/data_grid.vue'
import Drawer from '@/components/ui/drawer.vue'

// Protokoll & Historie (PRD §3.9) — Übermittlungen aus Backend (/api/uebermittlungen).
interface Uebermittlung {
  id: string
  datum: Date
  wj: string
  modus: 'Test' | 'Echt'
  status: string
  transfer_ticket: string
  benutzer: string
  rueckmeldung: string
}

const eintraege = ref<Uebermittlung[]>([])
const fehler = ref<string | null>(null)
async function laden() {
  try {
    const rows = await api.uebermittlungen()
    eintraege.value = rows.map((r) => ({
      id: String(r.id),
      datum: new Date(r.datum),
      wj: r.wj,
      modus: r.modus,
      status: r.status,
      transfer_ticket: r.transfer_ticket,
      benutzer: r.benutzer,
      rueckmeldung: r.rueckmeldung,
    }))
    fehler.value = null
  } catch (e) {
    fehler.value = e instanceof ApiError ? e.message : 'Protokoll konnte nicht geladen werden.'
  }
}
onMounted(laden)

const offen = ref(false)
const aktiv = ref<Uebermittlung | null>(null)
function oeffne(row: Uebermittlung) {
  aktiv.value = row
  offen.value = true
}

const columns: GridColumn[] = [
  { field: 'datum', header: 'Datum/Zeit', width: 170, sortable: true, format: (v) => formatDateTime(v as Date) },
  { field: 'wj', header: 'WJ', width: 90, filter: true },
  { field: 'modus', header: 'Modus', width: 90 },
  { field: 'status', header: 'Status', width: 170 },
  { field: 'transfer_ticket', header: 'Transfer-Ticket', width: 150, mono: true, filter: true },
  { field: 'pdf', header: 'ERiC-PDF', width: 110 },
  { field: 'benutzer', header: 'Durch', width: 140, filter: true },
]
</script>

<template>
  <div id="protokoll" class="space-y-4">
    <Banner v-if="fehler" id="protokoll-error" kind="error" titel="Protokoll konnte nicht geladen werden">
      {{ fehler }} — läuft das Backend?
    </Banner>
    <Banner id="protokoll-reminder" kind="info">
      Bundesanzeiger-Offenlegung ist separat erforderlich.
    </Banner>

    <DataGrid id="protokoll-grid" :columns="columns" :data="eintraege" row-key="id" max-height="56vh">
      <template #cell-modus="{ row }">
        <BadgePill :tone="(row as Uebermittlung).modus === 'Echt' ? 'success' : 'info'" :label="(row as Uebermittlung).modus" />
      </template>
      <template #cell-status="{ row }">
        <BadgePill :status="(row as Uebermittlung).status" />
      </template>
      <template #cell-pdf="{ row }">
        <TheButton variant="ghost" @click="oeffne(row as Uebermittlung)">PDF</TheButton>
      </template>
      <template #cell-benutzer="{ row, value }">
        <button :id="'open-' + (row as Uebermittlung).id" type="button" class="text-primary hover:underline" @click="oeffne(row as Uebermittlung)">
          {{ value }}
        </button>
      </template>
    </DataGrid>

    <!-- Detail-Drawer -->
    <Drawer id="protokoll-drawer" v-model="offen" :titel="aktiv ? 'Übermittlung ' + aktiv.transfer_ticket : ''">
      <div v-if="aktiv" id="protokoll-detail" class="space-y-4 text-sm">
        <div class="flex flex-wrap gap-2">
          <BadgePill :tone="aktiv.modus === 'Echt' ? 'success' : 'info'" :label="aktiv.modus" />
          <BadgePill :status="aktiv.status" />
        </div>
        <dl class="space-y-1">
          <div class="flex justify-between"><dt class="text-muted-foreground">Datum</dt><dd>{{ formatDateTime(aktiv.datum) }}</dd></div>
          <div class="flex justify-between"><dt class="text-muted-foreground">WJ</dt><dd>{{ aktiv.wj }}</dd></div>
          <div class="flex justify-between"><dt class="text-muted-foreground">Durch</dt><dd>{{ aktiv.benutzer }}</dd></div>
        </dl>
        <div>
          <p class="mb-1 font-medium">Rückmeldung</p>
          <p class="rounded-control border border-border bg-muted p-3">{{ aktiv.rueckmeldung }}</p>
        </div>
        <div id="protokoll-detail-actions" class="flex flex-wrap gap-2 pt-2">
          <TheButton variant="outline">XBRL herunterladen</TheButton>
          <TheButton variant="outline">PDF herunterladen</TheButton>
          <TheButton variant="secondary">Berichtigung erstellen</TheButton>
        </div>
      </div>
    </Drawer>
  </div>
</template>
