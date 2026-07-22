"""
Pass/fail rule evaluation: compares one window's train and test
`OverallPerformance` against a caller-supplied `ValidationRules` - no
threshold is hardcoded here, every comparison reads its limit from the
`rules` argument (see `docs/VALIDATION_GUIDE.md`'s "Acceptance
criteria"/"Failure criteria").

`compute_performance_degradation`/`compute_drawdown_increase` are
exposed separately (not just inlined into `evaluate_pass_fail`) so
`report.py` can reuse the exact same formula for its aggregate
statistics - one definition, not two that could drift.
"""

from app.trading.analytics.models import OverallPerformance
from app.validation.models import PassFailAssessment, RuleEvaluation, ValidationRules


def compute_performance_degradation(
    train: OverallPerformance, test: OverallPerformance
) -> float | None:
    """
    Percent by which test net profit is worse than train net profit.
    Positive means test underperformed train; negative means test
    outperformed train. `None` when train net profit is exactly zero -
    there is no meaningful percentage to compute against a zero base.
    """
    if train.net_profit == 0:
        return None
    return (train.net_profit - test.net_profit) / abs(train.net_profit) * 100


def compute_drawdown_increase(train: OverallPerformance, test: OverallPerformance) -> float | None:
    """
    Percent by which test max drawdown is worse (larger) than train's.
    `None` when train had zero drawdown - there is no meaningful
    percentage increase over a zero base (see `evaluate_pass_fail`,
    which treats this case as a hard fail whenever test drawdown is
    nonzero, since any drawdown is an infinite increase over none).
    """
    if train.max_drawdown == 0:
        return None
    return (test.max_drawdown - train.max_drawdown) / train.max_drawdown * 100


def evaluate_pass_fail(
    train: OverallPerformance, test: OverallPerformance, rules: ValidationRules
) -> PassFailAssessment:
    evaluations = [
        _evaluate_drawdown_increase(train, test, rules),
        _evaluate_profit_factor(test, rules),
        _evaluate_performance_degradation(train, test, rules),
        _evaluate_trade_count(test, rules),
    ]
    return PassFailAssessment(
        passed=all(evaluation.passed for evaluation in evaluations),
        evaluations=tuple(evaluations),
    )


def _evaluate_drawdown_increase(
    train: OverallPerformance, test: OverallPerformance, rules: ValidationRules
) -> RuleEvaluation:
    increase = compute_drawdown_increase(train, test)

    if increase is None:
        passed = test.max_drawdown == 0
        detail = (
            f"train had zero drawdown; test drawdown={test.max_drawdown}"
            f" ({'no increase' if passed else 'any drawdown over zero fails'})"
        )
    else:
        passed = increase <= rules.max_drawdown_increase_percent
        detail = (
            f"drawdown increased {increase:.2f}% "
            f"(limit {rules.max_drawdown_increase_percent:.2f}%)"
        )

    return RuleEvaluation(
        rule_name="max_drawdown_increase_percent", passed=passed, detail=detail
    )


def _evaluate_profit_factor(test: OverallPerformance, rules: ValidationRules) -> RuleEvaluation:
    if test.profit_factor is None:
        return RuleEvaluation(
            rule_name="min_profit_factor",
            passed=False,
            detail="test profit factor is undefined (no losing trades to divide by, or no "
            "trades) - cannot verify this rule",
        )

    passed = test.profit_factor >= rules.min_profit_factor
    return RuleEvaluation(
        rule_name="min_profit_factor",
        passed=passed,
        detail=(
            f"test profit factor={test.profit_factor:.4f} "
            f"(minimum {rules.min_profit_factor:.4f})"
        ),
    )


def _evaluate_performance_degradation(
    train: OverallPerformance, test: OverallPerformance, rules: ValidationRules
) -> RuleEvaluation:
    degradation = compute_performance_degradation(train, test)

    if degradation is None:
        passed = test.net_profit >= 0
        reason = "no degradation from zero" if passed else "negative result over a zero base fails"
        detail = f"train had zero net profit; test net profit={test.net_profit} ({reason})"
    else:
        passed = degradation <= rules.max_performance_degradation_percent
        detail = (
            f"performance degraded {degradation:.2f}% "
            f"(limit {rules.max_performance_degradation_percent:.2f}%)"
        )

    return RuleEvaluation(
        rule_name="max_performance_degradation_percent", passed=passed, detail=detail
    )


def _evaluate_trade_count(test: OverallPerformance, rules: ValidationRules) -> RuleEvaluation:
    passed = test.total_trades >= rules.min_trade_count
    return RuleEvaluation(
        rule_name="min_trade_count",
        passed=passed,
        detail=f"test total_trades={test.total_trades} (minimum {rules.min_trade_count})",
    )
