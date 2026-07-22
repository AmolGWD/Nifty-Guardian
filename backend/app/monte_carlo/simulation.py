"""
Runs one Monte Carlo simulation: applies whichever perturbations
`PerturbationConfig` enables, in a single fixed order (trade shuffle,
slippage, commission, execution delay, missed trades, position
variation), then measures the resulting outcome.

The fixed order matters for reproducibility (the same seed must always
produce the same result) but is otherwise a reasonable, documented
choice, not the only valid one - see docs/MONTE_CARLO_GUIDE.md.

Reuses `app.trading.backtest.performance.calculate_max_drawdown`
directly - the one piece of existing Analytics arithmetic that applies
unchanged to a perturbed trade sequence. `calculate_sharpe_ratio`/
`build_performance_report` are deliberately NOT reused here: both
group by calendar date, which becomes meaningless once trade order has
been shuffled away from real chronological order - this module builds
its own minimal, order-based equity curve instead (cumulative pnl in
list order, not sorted by timestamp), which is exactly what
`calculate_max_drawdown` itself already expects (it never reads
`EquityPoint.timestamp`, only `.equity`, in list order).
"""

import random
from datetime import datetime

from app.market_data.schemas import Candle
from app.monte_carlo.models import PerturbationConfig, SimulationResult
from app.monte_carlo.perturbations import (
    commission,
    execution_delay,
    missed_trade,
    position_variation,
    slippage,
    trade_shuffle,
)
from app.trading.backtest.models import BacktestTrade, EquityPoint
from app.trading.backtest.performance import calculate_max_drawdown


def run_one_simulation(
    trades: list[BacktestTrade],
    *,
    initial_capital: float,
    perturbation_config: PerturbationConfig,
    rng: random.Random,
    candles: list[Candle] | None,
    simulation_index: int = 0,
) -> SimulationResult:
    perturbed = list(trades)

    if perturbation_config.trade_shuffle_enabled:
        perturbed = trade_shuffle.apply(perturbed, rng)

    if perturbation_config.slippage is not None:
        perturbed = slippage.apply(perturbed, perturbation_config.slippage)

    if perturbation_config.commission is not None:
        perturbed = commission.apply(perturbed, perturbation_config.commission)

    if perturbation_config.execution_delay is not None:
        if candles is None:
            raise ValueError("execution_delay perturbation requires the original candles")
        perturbed = execution_delay.apply(perturbed, candles, perturbation_config.execution_delay)

    if perturbation_config.missed_trades is not None:
        perturbed = missed_trade.apply(perturbed, perturbation_config.missed_trades, rng)

    if perturbation_config.position_variation is not None:
        perturbed = position_variation.apply(
            perturbed, perturbation_config.position_variation, rng
        )

    equity_curve = _build_equity_curve(perturbed, initial_capital)
    final_capital = equity_curve[-1].equity
    net_profit = final_capital - initial_capital
    total_return_percent = (net_profit / initial_capital * 100) if initial_capital else 0.0
    max_drawdown = calculate_max_drawdown(equity_curve)

    return SimulationResult(
        simulation_index=simulation_index,
        final_capital=round(final_capital, 4),
        net_profit=round(net_profit, 4),
        total_return_percent=round(total_return_percent, 4),
        max_drawdown=round(max_drawdown, 4),
        total_trades=len(perturbed),
    )


def _build_equity_curve(trades: list[BacktestTrade], initial_capital: float) -> list[EquityPoint]:
    equity = initial_capital
    points = [EquityPoint(timestamp=_first_timestamp(trades), equity=equity)]
    for trade in trades:
        equity += trade.pnl
        points.append(EquityPoint(timestamp=trade.exit_time, equity=equity))
    return points


def _first_timestamp(trades: list[BacktestTrade]) -> datetime:
    return trades[0].entry_time if trades else datetime.now()
