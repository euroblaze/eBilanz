import { defineStore } from 'pinia'
import { api } from '@/libs/api'

// Das zentrale Arbeitsobjekt: E-Bilanz-Projekt = 1 Wirtschaftsjahr (WJ).
// Fast aller App-State ist auf das aktive WJ bezogen (PRD §0/§2.1 WJ-Selector).
export interface WirtschaftsjahrProjekt {
  id: string
  bezeichnung: string // z. B. "WJ 2024"
  von: Date
  bis: Date
  taxonomieVersion: string // z. B. "6.9"
  taxonomieLabel: string // z. B. "Kern 6.9 + JAbschlVUV"
  status: string // siehe PRD §1.3 Statuswerte
}

// Mock-Daten (kein Backend in diesem Slice).
const MOCK_PROJEKTE: WirtschaftsjahrProjekt[] = [
  {
    id: 'wj-2024',
    bezeichnung: 'WJ 2024',
    von: new Date(2024, 0, 1),
    bis: new Date(2024, 11, 31),
    taxonomieVersion: '6.9',
    taxonomieLabel: 'Kern 6.9 + JAbschlVUV',
    status: 'In Bearbeitung',
  },
  {
    id: 'wj-2023',
    bezeichnung: 'WJ 2023',
    von: new Date(2023, 0, 1),
    bis: new Date(2023, 11, 31),
    taxonomieVersion: '6.9',
    taxonomieLabel: 'Kern 6.9',
    status: 'Echtfall gesendet',
  },
]

export const useWjStore = defineStore('wj', {
  state: () => ({
    projekte: MOCK_PROJEKTE as WirtschaftsjahrProjekt[],
    aktivesProjektId: 'wj-2024' as string,
    // Status der Datenquellen / Sidecar (ericVersion noch Mock; odooVerbunden aus /health).
    ericVersion: '41.2',
    ericAktiv: true,
    odooVerbunden: true,
    odooDb: '' as string,
    geladen: false,
    ladeFehler: null as string | null,
  }),
  getters: {
    aktivesProjekt(state): WirtschaftsjahrProjekt {
      return (
        state.projekte.find((p) => p.id === state.aktivesProjektId) ?? state.projekte[0]
      )
    },
  },
  actions: {
    setAktivesProjekt(id: string) {
      this.aktivesProjektId = id
    },
    // Wirtschaftsjahre + Datenquellen-Status vom Backend laden (Mock als Fallback).
    async laden() {
      try {
        const [wjs, health] = await Promise.all([api.wirtschaftsjahre(), api.health()])
        this.projekte = wjs.map((w) => ({
          id: String(w.id),
          bezeichnung: w.bezeichnung,
          von: new Date(w.von),
          bis: new Date(w.bis),
          taxonomieVersion: w.taxonomie_version,
          taxonomieLabel: w.taxonomie_label,
          status: w.status,
        }))
        if (this.projekte.length && !this.projekte.find((p) => p.id === this.aktivesProjektId)) {
          this.aktivesProjektId = this.projekte[0].id
        }
        this.odooVerbunden = health.odoo_configured
        this.odooDb = health.odoo_db ?? ''
        this.ladeFehler = null
        this.geladen = true
      } catch (e) {
        // Backend nicht erreichbar -> Mock-Daten bleiben aktiv.
        this.ladeFehler = e instanceof Error ? e.message : 'Backend nicht erreichbar.'
      }
    },
  },
})
