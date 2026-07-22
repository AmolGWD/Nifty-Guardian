import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EngineControls } from './EngineControls'
import * as hooks from '../../hooks'
import type { EngineControls as EngineControlsHookResult } from '../../hooks'

function mockControls(overrides: Partial<EngineControlsHookResult> = {}) {
  const controls: EngineControlsHookResult = {
    sessionState: 'NotStarted',
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    stop: vi.fn(),
    replay: vi.fn(),
    reset: vi.fn(),
    ...overrides,
  }
  vi.spyOn(hooks, 'useEngineControls').mockReturnValue(controls)
  return controls
}

describe('EngineControls', () => {
  it('only enables Start when NotStarted', () => {
    mockControls({ sessionState: 'NotStarted' })
    render(<EngineControls />)

    expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Resume' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Replay' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled()
  })

  it('enables Pause and Stop when Running', () => {
    mockControls({ sessionState: 'Running' })
    render(<EngineControls />)

    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Resume' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeEnabled()
  })

  it('enables Resume and Stop when Paused', () => {
    mockControls({ sessionState: 'Paused' })
    render(<EngineControls />)

    expect(screen.getByRole('button', { name: 'Resume' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Stop' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled()
  })

  it('enables Replay when Stopped or Ended', () => {
    mockControls({ sessionState: 'Stopped' })
    const { rerender } = render(<EngineControls />)
    expect(screen.getByRole('button', { name: 'Replay' })).toBeEnabled()

    mockControls({ sessionState: 'Ended' })
    rerender(<EngineControls />)
    expect(screen.getByRole('button', { name: 'Replay' })).toBeEnabled()
  })

  it('calls the matching service action when a button is clicked - no logic in between', async () => {
    const controls = mockControls({ sessionState: 'Running' })
    const user = userEvent.setup()
    render(<EngineControls />)

    await user.click(screen.getByRole('button', { name: 'Pause' }))
    expect(controls.pause).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: 'Stop' }))
    expect(controls.stop).toHaveBeenCalledTimes(1)
  })
})
