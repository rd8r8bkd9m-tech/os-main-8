import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.KOLIBRI_PUBLIC_BASE_URL || './',
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
})
