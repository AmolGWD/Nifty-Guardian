import { Badge, DataTable, Panel, StatRow, orderStatusTone } from '../Common'
import { useOrders } from '../../hooks'
import type { Order } from '../../types'

const OPEN_STATUSES = new Set(['New', 'Validated', 'Submitted', 'PartiallyFilled'])

/** Open Orders, Filled Orders, Rejected Orders, Order Status. */
export function OrdersPanel() {
  const orders = useOrders()

  const openCount = orders.filter((order) => OPEN_STATUSES.has(order.status)).length
  const filledCount = orders.filter((order) => order.status === 'Filled').length
  const rejectedCount = orders.filter((order) => order.status === 'Rejected').length

  return (
    <Panel title="Orders">
      <StatRow label="Open" value={openCount} />
      <StatRow label="Filled" value={filledCount} />
      <StatRow label="Rejected" value={rejectedCount} />
      <DataTable<Order>
        columns={[
          { key: 'strategy', header: 'Strategy', render: (order) => order.strategyName },
          { key: 'direction', header: 'Dir', render: (order) => order.direction },
          {
            key: 'quantity',
            header: 'Qty',
            align: 'right',
            render: (order) => `${order.filledQuantity}/${order.requestedQuantity}`,
          },
          {
            key: 'price',
            header: 'Price',
            align: 'right',
            render: (order) => (order.averageFillPrice ?? order.requestedPrice).toFixed(2),
          },
          {
            key: 'status',
            header: 'Status',
            render: (order) => <Badge tone={orderStatusTone(order.status)}>{order.status}</Badge>,
          },
        ]}
        rows={orders}
        getRowKey={(order) => order.orderId}
        emptyMessage="No orders yet."
      />
    </Panel>
  )
}
