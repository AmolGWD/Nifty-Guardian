"""
Drawdown episode detection: Phase 11's PerformanceReport only reports
the single deepest drawdown; this walks the equity curve once (O(n))
to find every distinct peak-to-recovery episode, for the "Drawdown
Distribution" and "Largest Equity Peak/Valley" analytics this phase
adds.

An episode starts wherever equity first dips below the running peak,
troughs at its lowest point, and ends when equity recovers back to (or
above) that peak - or never ends, if the data runs out while still
underwater (`recovery_time=None`).
"""

from app.trading.analytics.models import DrawdownEpisode
from app.trading.backtest.models import EquityPoint


def identify_drawdown_episodes(equity_curve: list[EquityPoint]) -> list[DrawdownEpisode]:
    if not equity_curve:
        return []

    episodes: list[DrawdownEpisode] = []

    peak = equity_curve[0]
    in_drawdown = False
    trough = equity_curve[0]

    for point in equity_curve:
        if point.equity >= peak.equity:
            if in_drawdown:
                episodes.append(_build_episode(peak, trough, point))
                in_drawdown = False
            peak = point
            trough = point
            continue

        if not in_drawdown:
            in_drawdown = True
            trough = point
        elif point.equity < trough.equity:
            trough = point

    if in_drawdown:
        episodes.append(_build_episode(peak, trough, None))

    return episodes


def _build_episode(
    peak: EquityPoint, trough: EquityPoint, recovery: EquityPoint | None
) -> DrawdownEpisode:
    depth = peak.equity - trough.equity
    depth_percent = (depth / peak.equity * 100) if peak.equity else 0.0

    return DrawdownEpisode(
        peak_time=peak.timestamp,
        trough_time=trough.timestamp,
        recovery_time=recovery.timestamp if recovery is not None else None,
        depth=round(depth, 4),
        depth_percent=round(depth_percent, 4),
    )
