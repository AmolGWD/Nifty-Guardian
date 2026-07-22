import { Header } from '../../components/Header'
import { EngineControls } from '../../components/Controls'
import { MarketPanel, ChartPlaceholder } from '../../components/Market'
import { HealthPanel } from '../../components/Health'
import { TradingPanel } from '../../components/Trading'
import { OrdersPanel } from '../../components/Orders'
import { PositionsPanel } from '../../components/Positions'
import { PortfolioPanel } from '../../components/Portfolio'
import { RuntimePanel } from '../../components/Runtime'
import { JournalPanel } from '../../components/Journal'
import { SignalStatePanel, DummyTradesPanel, PerformancePanel } from '../../components/Signals'
import styles from './DashboardPage.module.css'

/**
 * Four-column operational console: Left (Controls/Market/Health),
 * Center (Chart/Trading/Orders/Positions), Right (Portfolio/Runtime/
 * Journal), Signals (Signal Engine/Dummy Trades/Performance) - the
 * original three columns are the CTO brief's exact Phase 21 LAYOUT
 * specification, untouched; the fourth is this phase's own addition
 * for the Guardian Score/dummy trade/performance reporting a later
 * CTO brief explicitly commissioned. No business logic lives in this
 * file; it only arranges panels that each read from their own store
 * via their own hook.
 */
export function DashboardPage() {
  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.columns}>
        <div className={styles.column}>
          <EngineControls />
          <MarketPanel />
          <HealthPanel />
        </div>
        <div className={styles.column}>
          <ChartPlaceholder />
          <TradingPanel />
          <OrdersPanel />
          <PositionsPanel />
        </div>
        <div className={styles.column}>
          <PortfolioPanel />
          <RuntimePanel />
          <JournalPanel />
        </div>
        <div className={styles.column}>
          <SignalStatePanel />
          <DummyTradesPanel />
          <PerformancePanel />
        </div>
      </div>
    </div>
  )
}
