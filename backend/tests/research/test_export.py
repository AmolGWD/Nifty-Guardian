import csv
import json

from app.research.export import export_csv, export_json, export_markdown
from app.research.models import Metric
from app.research.ranking import rank_experiments
from tests.research.helpers import make_synthetic_result


def test_export_json_includes_summary_fields(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = make_synthetic_result(name="A", net_profit=1000.0)
    path = tmp_path / "summary.json"

    export_json([result], path)

    data = json.loads(path.read_text())
    assert len(data) == 1
    assert data[0]["name"] == "A"
    assert data[0]["NetProfit"] == 1000.0
    assert data[0]["experiment_id"] == result.experiment.experiment_id


def test_export_json_includes_parameters_with_prefix(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = make_synthetic_result(name="A")
    # replace experiment with one carrying parameters
    experiment = result.experiment.model_copy(update={"parameters": {"ema_period": 20}})
    result = result.model_copy(update={"experiment": experiment})
    path = tmp_path / "summary.json"

    export_json([result], path)

    data = json.loads(path.read_text())
    assert data[0]["param_ema_period"] == 20


def test_export_csv_has_consistent_columns_across_rows(tmp_path) -> None:  # type: ignore[no-untyped-def]
    a = make_synthetic_result(name="A", net_profit=1000.0)
    b = make_synthetic_result(name="B", net_profit=2000.0)
    path = tmp_path / "summary.csv"

    export_csv([a, b], path)

    with open(path, newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert set(rows[0].keys()) == set(rows[1].keys())
    assert rows[0]["name"] == "A"
    assert rows[1]["name"] == "B"


def test_export_csv_handles_empty_results(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "empty.csv"

    export_csv([], path)

    assert path.read_text() == ""


def test_export_markdown_includes_ranking_and_details(tmp_path) -> None:  # type: ignore[no-untyped-def]
    low = make_synthetic_result(name="Low", net_profit=500.0)
    high = make_synthetic_result(name="High", net_profit=5000.0)
    ranked = rank_experiments([low, high], Metric.NET_PROFIT)
    path = tmp_path / "summary.md"

    export_markdown([low, high], path, ranking=ranked)

    content = path.read_text()
    assert "# Experiment Summary" in content
    assert "High" in content
    assert "Low" in content
    assert "## Details" in content
    # High should be ranked #1 since it's listed first in `ranked`
    assert content.index("High") < content.index("Low")
