import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// VITE_BASE_PATH:
//   '/'        — local dev and EC2 production (default)
//   '/Mosaic/' — GitHub Pages static showcase build (set in pages.yml CI)
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH ?? '/',
})
