import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // In ascolto su tutte le interfacce (necessario dentro il container).
    host: true,
    port: 5173,
    // Proxy verso il backend in sviluppo: evita problemi di CORS
    // senza dover modificare FastAPI. In locale punta a localhost:8000;
    // in Docker viene sovrascritto con http://backend:8000 (VITE_PROXY_TARGET).
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Con bind mount in container il file-watching nativo può non scattare:
    // VITE_USE_POLLING abilita il polling.
    watch: process.env.VITE_USE_POLLING === 'true' ? { usePolling: true } : undefined,
  },
})
