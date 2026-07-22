import { Badge, EmptyState, Panel, StatRow } from '../Common'
import { useTradingSignal } from '../../hooks'
import styles from './TradingPanel.module.css'

/**
 * Latest Signal, Risk Decision, Trade Recommendation, Confidence.
 * "Confidence" is always `StrategyEvaluation.strength`/
 * `TradeRecommendation.recommendationStrength` - the backend's own
 * coarse Strong/Moderate/Weak read (app.trading.strategy.models,
 * app.trading.decision.models, both frozen) - never a percentage this
 * dashboard invents, per the CTO brief's "Confidence (from backend
 * only)".
 */
export function TradingPanel() {
  const { latestSignal, latestRiskDecision, latestRecommendation } = useTradingSignal()

  return (
    <Panel title="Trading">
      <div className={styles.section}>
        <div className={styles.sectionTitle}>Latest Signal</div>
        {latestSignal ? (
          <>
            <StatRow label="Strategy" value={latestSignal.strategyName} />
            <StatRow
              label="Valid"
              value={
                <Badge tone={latestSignal.valid ? 'positive' : 'neutral'}>
                  {String(latestSignal.valid)}
                </Badge>
              }
            />
            <StatRow label="Direction" value={latestSignal.direction} />
            <StatRow label="Confidence" value={latestSignal.strength} />
          </>
        ) : (
          <EmptyState message="No signal yet." />
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Risk Decision</div>
        {latestRiskDecision ? (
          <>
            <StatRow
              label="Risk OK"
              value={
                <Badge tone={latestRiskDecision.riskOk ? 'positive' : 'negative'}>
                  {String(latestRiskDecision.riskOk)}
                </Badge>
              }
            />
            <StatRow label="Position Size" value={latestRiskDecision.positionSize} />
            <StatRow label="Stop Loss" value={latestRiskDecision.stopLoss.toFixed(2)} />
            <StatRow label="Target" value={latestRiskDecision.target.toFixed(2)} />
            <StatRow label="Reward:Risk" value={latestRiskDecision.rewardRiskRatio.toFixed(2)} />
          </>
        ) : (
          <EmptyState message="No risk assessment yet." />
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Trade Recommendation</div>
        {latestRecommendation ? (
          <>
            <StatRow
              label="Recommended"
              value={
                <Badge tone={latestRecommendation.recommended ? 'positive' : 'neutral'}>
                  {String(latestRecommendation.recommended)}
                </Badge>
              }
            />
            <StatRow label="Strategy" value={latestRecommendation.selectedStrategy ?? '-'} />
            <StatRow
              label="Confidence"
              value={latestRecommendation.recommendationStrength ?? '-'}
            />
            {latestRecommendation.reasons.length > 0 && (
              <ul className={styles.reasons}>
                {latestRecommendation.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <EmptyState message="No recommendation yet." />
        )}
      </div>
    </Panel>
  )
}
