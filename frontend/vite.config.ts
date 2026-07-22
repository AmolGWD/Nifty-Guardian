/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // dashboard_mock_data.json lives in ../scripts/ (repo root), alongside
    // every other phase's demo script - the dev server's file-serving
    // allow-list otherwise defaults to this package's own root.
    fs: { allow: ['..'] },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    globals: false,
    css: false,
  },
})
