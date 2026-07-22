/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_DASHBOARD_SERVICE?: string
  readonly VITE_DASHBOARD_POLLING_INTERVAL_MS?: string
  readonly VITE_API_TIMEOUT_MS?: string
  readonly VITE_DEFAULT_REPLAY_SPEED?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
