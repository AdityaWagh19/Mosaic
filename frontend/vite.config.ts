import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
// VITE_BASE_PATH:
//   '/'        — local dev and EC2 production (default)
//   '/Mosaic/' — GitHub Pages static showcase build (set in pages.yml CI)
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH ?? '/',
  resolve: {
    alias: {
      'three': path.resolve(__dirname, './node_modules/three')
    },
  },
})
