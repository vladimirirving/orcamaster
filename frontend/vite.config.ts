import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/usuarios': 'http://localhost:8000',
      '/obras': 'http://localhost:8000',
      '/versoes': 'http://localhost:8000',
      '/grupos': 'http://localhost:8000',
      '/itens': 'http://localhost:8000',
      '/bdi': 'http://localhost:8000',
      '/composicoes': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/agente': 'http://localhost:8000',
    },
  },
})
