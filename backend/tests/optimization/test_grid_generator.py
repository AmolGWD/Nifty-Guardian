from app.optimization.grid_generator import generate_grid
from app.optimization.parameter_space import (
    EMA_PERIOD,
    REWARD_RISK_RATIO,
    RSI_BULLISH_THRESHOLD,
    ParameterSpace,
)


def test_single_dimension_grid_matches_parameter_values() -> None:
    space = ParameterSpace(parameters=(RSI_BULLISH_THRESHOLD,))

    grid = generate_grid(space)

    assert grid == (
        {"rsi_bullish_threshold": 50.0},
        {"rsi_bullish_threshold": 55.0},
        {"rsi_bullish_threshold": 60.0},
    )


def test_cartesian_product_size_matches_total_combinations() -> None:
    space = ParameterSpace(parameters=(RSI_BULLISH_THRESHOLD, REWARD_RISK_RATIO))

    grid = generate_grid(space)

    assert len(grid) == space.total_combinations() == 9


def test_cartesian_product_covers_every_combination_exactly_once() -> None:
    space = ParameterSpace(parameters=(RSI_BULLISH_THRESHOLD, REWARD_RISK_RATIO))

    grid = generate_grid(space)

    seen = {(combo["rsi_bullish_threshold"], combo["reward_risk_ratio"]) for combo in grid}
    expected = {
        (rsi, rr) for rsi in RSI_BULLISH_THRESHOLD.values() for rr in REWARD_RISK_RATIO.values()
    }
    assert seen == expected
    assert len(grid) == len(seen)


def test_grid_generation_is_deterministic_across_calls() -> None:
    space = ParameterSpace(parameters=(EMA_PERIOD, RSI_BULLISH_THRESHOLD))

    first = generate_grid(space)
    second = generate_grid(space)

    assert first == second


def test_last_parameter_varies_fastest() -> None:
    space = ParameterSpace(parameters=(RSI_BULLISH_THRESHOLD, REWARD_RISK_RATIO))

    grid = generate_grid(space)

    assert grid[0] == {"rsi_bullish_threshold": 50.0, "reward_risk_ratio": 1.5}
    assert grid[1] == {"rsi_bullish_threshold": 50.0, "reward_risk_ratio": 2.0}
    assert grid[3] == {"rsi_bullish_threshold": 55.0, "reward_risk_ratio": 1.5}
