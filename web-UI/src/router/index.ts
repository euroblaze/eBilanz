import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppShell from '@/layouts/app_shell.vue'

// Routen aus PRD §2.2 (Hauptmenue) + §2.3 (Admin).
// In diesem Slice gerendert: /dashboard, /stammdaten. Rest = Platzhalter.
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard_view.vue'),
        meta: { titel: 'Übersicht' },
      },
      {
        path: 'stammdaten',
        name: 'stammdaten',
        component: () => import('@/views/stammdaten_view.vue'),
        meta: { titel: 'Stammdaten (GCD)' },
      },
      {
        path: 'import',
        name: 'import',
        component: () => import('@/views/saldenimport_view.vue'),
        meta: { titel: 'Saldenimport' },
      },
      {
        path: 'mapping',
        name: 'mapping',
        component: () => import('@/views/mapping_view.vue'),
        meta: { titel: 'Konten-Mapping' },
      },
      {
        path: 'gaap/:bestandteil?',
        name: 'gaap',
        component: () => import('@/views/gaap_view.vue'),
        meta: { titel: 'E-Bilanz Erfassung' },
      },
      {
        path: 'kontennachweise',
        name: 'kontennachweise',
        component: () => import('@/views/kontennachweise_view.vue'),
        meta: { titel: 'Kontennachweise' },
      },
      {
        path: 'validierung',
        name: 'validierung',
        component: () => import('@/views/validierung_view.vue'),
        meta: { titel: 'Validierung' },
      },
      {
        path: 'uebermittlung',
        name: 'uebermittlung',
        component: () => import('@/views/uebermittlung_view.vue'),
        meta: { titel: 'Übermittlung' },
      },
      {
        path: 'protokoll',
        name: 'protokoll',
        component: () => import('@/views/protokoll_view.vue'),
        meta: { titel: 'Protokoll & Historie' },
      },
      // Platzhalter — restliche Views folgen in spaeteren Slices (PRD §3/§4).
      {
        path: ':pathMatch(.*)*',
        name: 'platzhalter',
        component: () => import('@/views/placeholder_view.vue'),
        meta: { titel: 'In Vorbereitung' },
      },
    ],
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
