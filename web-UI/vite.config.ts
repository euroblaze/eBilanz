import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Dev-Server an Netzwerk-IP / Loopback-Alias binden (nicht localhost), CORS aktiv.
// Siehe globale Konventionen: Backends/Frontends laufen auf der Netzwerk-IP.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0', // erreichbar via 10.0.99.1 (Loopback-Alias) und Netzwerk-IP
    port: 5173,
    cors: true,
  },
})
