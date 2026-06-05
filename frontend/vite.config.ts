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
    proxy: Object.fromEntries(
      ['/auth', '/usuarios', '/obras', '/versoes', '/grupos', '/itens', '/bdi', '/composicoes', '/dashboard', '/agente'].map(
        path => [path, {
          target: 'http://localhost:8000',
          bypass(req: any) {
            if (req.headers.accept?.includes('text/html')) return '/index.html'
          },
        }]
      )
    ),
  },
})
