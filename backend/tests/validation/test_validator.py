from app.trading.analytics.models import OverallPerformance
from app.validation.models import ValidationRules
from app.validation.validator import (
    compute_drawdown_increase,
    compute_performance_degradation,
    evaluate_pass_fail,
)


def _overall(
    *,
    net_profit: float = 1000.0,
    max_drawdown: float = 500.0,
    profit_factor: float | None = 2.0,
    total_trades: int = 20,
) -> OverallPerformance:
    return OverallPerformance(
        initial_capital=100_000.0,
        final_capital=100_000.0 + net_profit,
        cagr=None,
        annual_return=None,
        net_profit=net_profit,
        total_return_percent=net_profit / 100_000.0 * 100,
        total_trades=total_trades,
        winning_trades=max(total_trades - 2, 0),
        losing_trades=min(total_trades, 2),
        win_rate=60.0,
        profit_factor=profit_factor,
        expectancy=net_profit / total_trades if total_trades else 0.0,
        average_win=200.0,
        average_loss=-100.0,
        largest_win=400.0,
        largest_loss=-200.0,
        reward_risk=2.0,
        sharpe_ratio=1.5,
        sortino_ratio=None,
        calmar_ratio=None,
        recovery_factor=2.0,
        max_drawdown=max_drawdown,
    )


_RULES = ValidationRules(
    max_drawdown_increase_percent=50.0,
    min_profit_factor=1.2,
    max_performance_degradation_percent=30.0,
    min_trade_count=5,
    min_robustness_score_percent=60.0,
)


def test_compute_performance_degradation_positive_when_test_worse() -> None:
    train = _overall(net_profit=1000.0)
    test = _overall(net_profit=500.0)

    assert compute_performance_degradation(train, test) == 50.0


def test_compute_performance_degradation_negative_when_test_better() -> None:
    train = _overall(net_profit=1000.0)
    test = _overall(net_profit=1500.0)

    assert compute_performance_degradation(train, test) == -50.0


def test_compute_performance_degradation_none_when_train_net_profit_zero() -> None:
    train = _overall(net_profit=0.0)
    test = _overall(net_profit=100.0)

    assert compute_performance_degradation(train, test) is None


def test_compute_drawdown_increase_positive_when_test_worse() -> None:
    train = _overall(max_drawdown=100.0)
    test = _overall(max_drawdown=200.0)

    assert compute_drawdown_increase(train, test) == 100.0


def test_compute_drawdown_increase_none_when_train_drawdown_zero() -> None:
    train = _overall(max_drawdown=0.0)
    test = _overall(max_drawdown=50.0)

    assert compute_drawdown_increase(train, test) is None


def test_passes_when_everything_within_configured_limits() -> None:
    train = _overall(net_profit=1000.0, max_drawdown=200.0, profit_factor=2.0, total_trades=20)
    test = _overall(net_profit=900.0, max_drawdown=250.0, profit_factor=1.5, total_trades=15)

    assessment = evaluate_pass_fail(train, test, _RULES)

    assert assessment.passed is True
    assert all(evaluation.passed for evaluation in assessment.evaluations)


def test_fails_when_drawdown_increase_exceeds_limit() -> None:
    train = _overall(max_drawdown=100.0)
    test = _overall(max_drawdown=1000.0)  # +900%, limit is 50%

    assessment = evaluate_pass_fail(train, test, _RULES)

    assert assessment.passed is False
    drawdown_rule = next(
        e for e in assessment.evaluations if e.rule_name == "max_drawdown_increase_percent"
    )
    assert drawdown_rule.passed is False


def test_fails_when_profit_factor_below_minimum() -> None:
    train = _overall(profit_factor=2.0)
    test = _overall(profit_factor=1.0)  # below the 1.2 minimum

    assessment = evaluate_pass_fail(train, test, _RULES)

    assert assessment.passed is False
    rule = next(e for e in assessment.evaluations if e.rule_name == "min_profit_factor")
    assert rule.passed is False


def test_fails_when_profit_factor_is_undefined() -> None:
    train = _overall(profit_factor=2.0)
    test = _overall(profit_factor=None)

    assessment = evaluate_pass_fail(train, test, _RULES)

    rule = next(e for e in assessment.evaluations if e.rule_name == "min_profit_factor")
    assert rule.passed is False
    assert assessment.passed is False


def test_fails_when_performance_degrades_beyond_limit() -> None:
    train = _overall(net_profit=1000.0)
    test = _overall(net_profit=100.0)  # -90%, limit is 30%

    assessment = evaluate_pass_fail(train, test, _RULES)

    assert assessment.passed is False
    rule = next(
        e for e in assessment.evaluations if e.rule_name == "max_performance_degradation_percent"
    )
    assert rule.passed is False


def test_fails_when_trade_count_below_minimum() -> None:
    train = _overall(total_trades=20)
    test = _overall(total_trades=2)  # below the 5-trade minimum

    assessment = evaluate_pass_fail(train, test, _RULES)

    assert assessment.passed is False
    rule = next(e for e in assessment.evaluations if e.rule_name == "min_trade_count")
    assert rule.passed is False


def test_zero_train_drawdown_and_zero_test_drawdown_passes() -> None:
    train = _overall(max_drawdown=0.0)
    test = _overall(max_drawdown=0.0)

    assessment = evaluate_pass_fail(train, test, _RULES)

    rule = next(e for e in assessment.evaluations if e.rule_name == "max_drawdown_increase_percent")
    assert rule.passed is True


def test_zero_train_drawdown_and_nonzero_test_drawdown_fails() -> None:
    train = _overall(max_drawdown=0.0)
    test = _overall(max_drawdown=1.0)

    assessment = evaluate_pass_fail(train, test, _RULES)

    rule = next(e for e in assessment.evaluations if e.rule_name == "max_drawdown_increase_percent")
    assert rule.passed is False
