import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { OrdersPanel } from './OrdersPanel'
import * as hooks from '../../hooks'
import type { Order } from '../../types'

function makeOrder(overrides: Partial<Order> = {}): Order {
  return {
    orderId: 'order-1',
    strategyName: 'EMABreakout',
    direction: 'Long',
    requestedPrice: 100,
    requestedQuantity: 10,
    filledQuantity: 10,
    averageFillPrice: 100,
    stopLoss: 95,
    target: 110,
    status: 'Filled',
    rejectionReason: null,
    createdAt: '2026-01-05T09:15:00',
    updatedAt: '2026-01-05T09:15:00',
    ...overrides,
  }
}

describe('OrdersPanel', () => {
  it('renders the empty state when there are no orders', () => {
    vi.spyOn(hooks, 'useOrders').mockReturnValue([])
    render(<OrdersPanel />)

    expect(screen.getByText('No orders yet.')).toBeInTheDocument()
  })

  it('summarizes open/filled/rejected counts and lists each order', () => {
    vi.spyOn(hooks, 'useOrders').mockReturnValue([
      makeOrder({ orderId: 'order-1', status: 'Filled' }),
      makeOrder({ orderId: 'order-2', status: 'Submitted', filledQuantity: 0 }),
      makeOrder({ orderId: 'order-3', status: 'Rejected', filledQuantity: 0 }),
    ])
    render(<OrdersPanel />)

    expect(screen.getAllByText('EMABreakout')).toHaveLength(3)
    // "Filled"/"Rejected" also appear as StatRow summary labels, so
    // scope these to the table's status badges specifically.
    const table = screen.getByRole('table')
    expect(within(table).getByText('Filled')).toBeInTheDocument()
    expect(within(table).getByText('Submitted')).toBeInTheDocument()
    expect(within(table).getByText('Rejected')).toBeInTheDocument()
  })
})
