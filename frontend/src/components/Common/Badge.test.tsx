import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from './Badge'

describe('Badge', () => {
  it('renders its children', () => {
    render(<Badge tone="positive">Running</Badge>)
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('defaults to the neutral tone', () => {
    render(<Badge>Idle</Badge>)
    expect(screen.getByText('Idle')).toBeInTheDocument()
  })
})
