import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Panel } from './Panel'

describe('Panel', () => {
  it('renders its title and children', () => {
    render(
      <Panel title="Runtime">
        <p>body content</p>
      </Panel>,
    )

    expect(screen.getByText('Runtime')).toBeInTheDocument()
    expect(screen.getByText('body content')).toBeInTheDocument()
  })

  it('renders an optional status slot', () => {
    render(
      <Panel title="Runtime" status={<span>STATUS</span>}>
        <p>body</p>
      </Panel>,
    )

    expect(screen.getByText('STATUS')).toBeInTheDocument()
  })
})
