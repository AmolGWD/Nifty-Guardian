"""
Graceful shutdown: flush the journal, stop the scheduler (by stopping
the session, since `SynchronousScheduler.run()` already returned by
the time shutdown is called - there is no separate scheduler handle to
signal), close the session, and print a summary. Computes nothing new
- every figure printed already exists on `PortfolioManager`/
`PerformanceMonitor`/`HealthMonitor`.
"""

from dataclasses import dataclass

from app.paper_trading.execution_journal import JournalEntry
from app.paper_trading.models import Portfolio
from app.paper_trading.performance_monitor import PerformanceSnapshot
from app.runtime.health import HealthSnapshot
from app.runtime.session_controller import SessionState
from app.runtime.startup import RuntimeContext


@dataclass
class ShutdownSummary:
    journaled_entries: tuple[JournalEntry, ...]
    final_portfolio: Portfolio
    final_performance: PerformanceSnapshot
    final_health: HealthSnapshot


def shutdown_runtime(context: RuntimeContext) -> ShutdownSummary:
    # Flush journal - in-memory this phase, so "flushing" means reading
    # its complete, final state rather than writing anywhere external.
    journaled_entries = context.execution_journal.all_entries()

    # Stop scheduler / close session.
    if context.session_controller.state in (SessionState.RUNNING, SessionState.PAUSED):
        context.session_controller.stop()
    if context.session_controller.state == SessionState.STOPPED:
        context.session_controller.end_session()

    final_portfolio = context.portfolio_manager.snapshot()
    final_performance = context.performance_monitor.snapshot()
    final_health = context.health_monitor.snapshot()

    summary = ShutdownSummary(
        journaled_entries=journaled_entries,
        final_portfolio=final_portfolio,
        final_performance=final_performance,
        final_health=final_health,
    )
    _print_summary(summary)
    return summary


def _print_summary(summary: ShutdownSummary) -> None:
    print("\n--- Shutdown Summary ---")
    print(f"Journal entries recorded: {len(summary.journaled_entries)}")
    print(
        f"Final portfolio: cash={summary.final_portfolio.cash}, "
        f"total_equity={summary.final_portfolio.total_equity}, "
        f"drawdown={summary.final_portfolio.drawdown}"
    )
    print(
        f"Performance: orders_submitted={summary.final_performance.orders_submitted}, "
        f"fill_ratio={summary.final_performance.fill_ratio_percent}%, "
        f"win_rate={summary.final_performance.win_rate_percent}%"
    )
    print(
        f"Health: processed_candles={summary.final_health.processed_candles}, "
        f"uptime={summary.final_health.uptime_seconds:.3f}s, "
        f"state={summary.final_health.current_state.value}"
    )
