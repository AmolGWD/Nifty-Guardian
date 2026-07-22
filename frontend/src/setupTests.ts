import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// `globals: false` (vite.config.ts) means Testing Library's own
// auto-cleanup detection (which looks for a global `afterEach`) never
// fires, so each render() would otherwise accumulate in the DOM across
// tests in the same file - this registers it explicitly instead.
afterEach(() => {
  cleanup()
})
