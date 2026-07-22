import { useDashboardStore } from './useDashboardStore'
import type { Candle, MarketContext } from '../types'

export interface MarketData {
  currentCandle: Candle | null
  marketContext: MarketContext | null
}

export function useMarketData(): MarketData {
  const currentCandle = useDashboardStore((state) => state.snapshot.currentCandle)
  const marketContext = useDashboardStore((state) => state.snapshot.marketContext)
  return { currentCandle, marketContext }
}
