import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardPage } from './DashboardPage'

describe('DashboardPage', () => {
  it('renders the header and every panel from the three-column layout', () => {
    render(<DashboardPage />)

    // Header
    expect(screen.getByText('NIFTY GUARDIAN')).toBeInTheDocument()

    // Left column
    expect(screen.getByText('Engine Controls')).toBeInTheDocument()
    expect(screen.getByText('Market')).toBeInTheDocument()
    expect(screen.getByText('Health')).toBeInTheDocument()

    // Center column
    expect(screen.getByText('Chart')).toBeInTheDocument()
    expect(screen.getByText('Trading')).toBeInTheDocument()
    expect(screen.getByText('Orders')).toBeInTheDocument()
    expect(screen.getByText('Positions')).toBeInTheDocument()

    // Right column
    expect(screen.getByText('Portfolio')).toBeInTheDocument()
    expect(screen.getByText('Runtime')).toBeInTheDocument()
    expect(screen.getByText('Journal')).toBeInTheDocument()
  })

  it('starts every control disabled except Start, before the engine runs', () => {
    render(<DashboardPage />)

    expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled()
  })
})
