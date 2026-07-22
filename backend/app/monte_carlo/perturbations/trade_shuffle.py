"""
Trade Order Shuffle: randomly reorders the same set of completed
trades, unchanged - no trade's own entry/exit price, time, or pnl is
touched.

This tests a different question from every other perturbation here:
"could this exact same set of trades have produced a worse drawdown
path just from happening in a different sequence?" - since
`simulation.py` builds its equity curve by cumulative sum *in list
order*, not by each trade's own timestamp, reordering the list
directly changes the simulated equity path without needing to touch
any trade's own numbers.
"""

import random

from app.trading.backtest.models import BacktestTrade


def apply(trades: list[BacktestTrade], rng: random.Random) -> list[BacktestTrade]:
    shuffled = list(trades)
    rng.shuffle(shuffled)
    return shuffled
