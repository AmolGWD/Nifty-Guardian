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
import styles from './DashboardPage.module.css'

/**
 * Three-column operational console: Left (Controls/Market/Health),
 * Center (Chart/Trading/Orders/Positions), Right (Portfolio/Runtime/
 * Journal) - the exact layout the CTO brief's LAYOUT section
 * specifies. No business logic lives in this file; it only arranges
 * panels that each read from the store via their own hook.
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
      </div>
    </div>
  )
}
