import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { App } from './App'

describe('App', () => {
  it('renders the dashboard', () => {
    render(<App />)
    expect(screen.getByText('NIFTY GUARDIAN')).toBeInTheDocument()
  })
})
