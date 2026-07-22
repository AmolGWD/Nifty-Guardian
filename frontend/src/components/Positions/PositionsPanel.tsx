import { Badge, DataTable, Panel, pnlColor, positionStatusTone } from '../Common'
import { usePositions } from '../../hooks'
import type { Position } from '../../types'

/** Open Positions, Quantity, Entry, PnL. */
export function PositionsPanel() {
  const positions = usePositions()
  const openPositions = positions.filter((position) => position.status !== 'Closed')

  return (
    <Panel title="Positions">
      <DataTable<Position>
        columns={[
          { key: 'strategy', header: 'Strategy', render: (position) => position.strategyName },
          { key: 'direction', header: 'Dir', render: (position) => position.direction },
          {
            key: 'quantity',
            header: 'Qty',
            align: 'right',
            render: (position) => position.quantity,
          },
          {
            key: 'entry',
            header: 'Entry',
            align: 'right',
            render: (position) => position.averageEntryPrice.toFixed(2),
          },
          {
            key: 'pnl',
            header: 'Unrealized PnL',
            align: 'right',
            render: (position) => (
              <span style={{ color: pnlColor(position.unrealizedPnl) }}>
                {position.unrealizedPnl.toFixed(2)}
              </span>
            ),
          },
          {
            key: 'status',
            header: 'Status',
            render: (position) => (
              <Badge tone={positionStatusTone(position.status)}>{position.status}</Badge>
            ),
          },
        ]}
        rows={openPositions}
        getRowKey={(position) => position.positionId}
        emptyMessage="No open positions."
      />
    </Panel>
  )
}
