import { Badge, DataTable, EmptyState, Panel, StatRow, formatDateTime, pnlTone } from '../Common'
import { useSignalEngine } from '../../hooks'
import type { DummyTrade } from '../../types'
import styles from './DummyTradesPanel.module.css'

const EXIT_REASON_TONE = {
  Target: 'positive',
  StopLoss: 'negative',
  EndOfDay: 'neutral',
  Unknown: 'neutral',
} as const

/**
 * Open Dummy Trade + Closed Trades - every trade here is a paper
 * trade `app.signals.dummy_trade_tracker` (backend) created from an
 * already-filled `PaperBroker` order. No real order was ever placed.
 */
export function DummyTradesPanel() {
  const { trades } = useSignalEngine()

  const openTrade = trades.find((trade) => trade.status === 'Open') ?? null
  const closedTrades = trades
    .filter((trade) => trade.status === 'Closed')
    .sort((a, b) => (b.closedAt ?? '').localeCompare(a.closedAt ?? ''))

  return (
    <Panel title="Dummy Trades">
      <div className={styles.section}>
        <div className={styles.sectionTitle}>Open Dummy Trade</div>
        {openTrade ? (
          <>
            <StatRow label="Strategy" value={openTrade.strategyName} />
            <StatRow label="Direction" value={openTrade.direction} />
            <StatRow label="Entry" value={openTrade.entryPrice.toFixed(2)} />
            <StatRow label="SL" value={openTrade.stopLoss.toFixed(2)} />
            <StatRow label="Target" value={openTrade.target.toFixed(2)} />
            <StatRow label="Opened At" value={formatDateTime(openTrade.openedAt)} />
          </>
        ) : (
          <EmptyState message="No open dummy trade." />
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Closed Trades</div>
        <DataTable<DummyTrade>
          columns={[
            { key: 'strategy', header: 'Strategy', render: (t) => t.strategyName },
            { key: 'direction', header: 'Dir', render: (t) => t.direction },
            {
              key: 'entry',
              header: 'Entry',
              align: 'right',
              render: (t) => t.entryPrice.toFixed(2),
            },
            {
              key: 'exit',
              header: 'Exit',
              align: 'right',
              render: (t) => (t.exitPrice ?? 0).toFixed(2),
            },
            {
              key: 'pnl',
              header: 'PnL',
              align: 'right',
              render: (t) => (
                <span className={styles[pnlTone(t.pnl ?? 0)]}>{(t.pnl ?? 0).toFixed(2)}</span>
              ),
            },
            {
              key: 'r',
              header: 'R',
              align: 'right',
              render: (t) => (t.rMultiple ?? 0).toFixed(2),
            },
            {
              key: 'reason',
              header: 'Exit Reason',
              render: (t) =>
                t.exitReason ? (
                  <Badge tone={EXIT_REASON_TONE[t.exitReason]}>{t.exitReason}</Badge>
                ) : (
                  '-'
                ),
            },
          ]}
          rows={closedTrades}
          getRowKey={(t) => t.tradeId}
          emptyMessage="No closed trades yet."
        />
      </div>
    </Panel>
  )
}
