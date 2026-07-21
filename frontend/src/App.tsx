import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string

type HealthStatus = {
  status: string
  service: string
  environment: string
}

type ConnectionState = 'checking' | 'online' | 'offline'

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [connection, setConnection] = useState<ConnectionState>('checking')

  useEffect(() => {
    let cancelled = false

    async function checkHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`)

        if (!response.ok) {
          throw new Error(`Unexpected status ${response.status}`)
        }

        const data = (await response.json()) as HealthStatus

        if (!cancelled) {
          setHealth(data)
          setConnection('online')
        }
      } catch {
        if (!cancelled) {
          setConnection('offline')
        }
      }
    }

    checkHealth()

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="app">
      <h1>NIFTY Guardian v2</h1>
      <p className="tagline">Trade with Discipline. Not Emotion.</p>

      <section className="status-card">
        <h2>Backend Connection</h2>
        {connection === 'checking' && <p>Checking backend status...</p>}
        {connection === 'online' && health && (
          <ul>
            <li>
              Status: <strong>{health.status}</strong>
            </li>
            <li>Service: {health.service}</li>
            <li>Environment: {health.environment}</li>
          </ul>
        )}
        {connection === 'offline' && (
          <p className="offline">
            Backend is unreachable. Make sure it is running and VITE_API_BASE_URL is set correctly.
          </p>
        )}
      </section>
    </main>
  )
}

export default App
