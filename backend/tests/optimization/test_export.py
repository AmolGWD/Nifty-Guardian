import csv
import json

from app.optimization.export import export_csv, export_json, export_markdown
from app.optimization.ranking import RankBy, rank_optimization_results
from tests.optimization.helpers import make_optimization_result


def test_export_json_includes_grid_parameters_as_param_columns(tmp_path) -> None:  # type: ignore[no-untyped-def]
    results = [
        make_optimization_result(
            combination_id="c0", parameter_values={"ema_period": 14, "risk_percent": 1.0}
        )
    ]
    path = tmp_path / "results.json"

    export_json(results, path)

    data = json.loads(path.read_text())
    assert data[0]["param_ema_period"] == 14
    assert data[0]["param_risk_percent"] == 1.0


def test_export_csv_includes_rank_column_when_ranking_supplied(tmp_path) -> None:  # type: ignore[no-untyped-def]
    results = [
        make_optimization_result(combination_id="low", net_profit=1.0),
        make_optimization_result(combination_id="high", net_profit=100.0),
    ]
    ranking = rank_optimization_results(results, rank_by=RankBy.NET_PROFIT)
    path = tmp_path / "results.csv"

    export_csv(results, path, ranking=ranking)

    with open(path, newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    ranks_by_name = {row["name"]: row["rank"] for row in rows}
    assert ranks_by_name["high"] == "1"
    assert ranks_by_name["low"] == "2"


def test_export_markdown_produces_a_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    results = [make_optimization_result(combination_id="c0")]
    path = tmp_path / "results.md"

    export_markdown(results, path)

    content = path.read_text()
    assert "# Experiment Summary" in content


def test_export_without_ranking_still_works(tmp_path) -> None:  # type: ignore[no-untyped-def]
    results = [make_optimization_result(combination_id="c0")]
    path = tmp_path / "results.json"

    export_json(results, path)

    data = json.loads(path.read_text())
    assert data[0]["rank"] == ""
