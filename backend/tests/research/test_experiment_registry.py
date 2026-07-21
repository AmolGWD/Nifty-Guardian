from app.research.experiment_registry import ExperimentRegistry
from app.research.models import ExperimentStatus
from tests.research.helpers import make_test_experiment, make_test_result


def test_register_and_get_experiment() -> None:
    registry = ExperimentRegistry()
    experiment = make_test_experiment(name="A")

    registry.register(experiment)

    assert registry.get_experiment(experiment.experiment_id) == experiment


def test_get_experiment_returns_none_for_unknown_id() -> None:
    registry = ExperimentRegistry()
    assert registry.get_experiment("unknown") is None


def test_record_result_stores_both_experiment_and_result() -> None:
    registry = ExperimentRegistry()
    experiment = make_test_experiment(name="A")
    result = make_test_result(experiment=experiment, status=ExperimentStatus.COMPLETED)

    registry.record_result(result)

    assert registry.get_experiment(experiment.experiment_id) == experiment
    assert registry.get_result(experiment.experiment_id) == result


def test_all_experiments_and_all_results() -> None:
    registry = ExperimentRegistry()
    experiment_a = make_test_experiment(name="A")
    experiment_b = make_test_experiment(name="B")
    registry.register(experiment_a)
    registry.record_result(make_test_result(experiment=experiment_b))

    all_experiments = registry.all_experiments()
    assert {e.experiment_id for e in all_experiments} == {
        experiment_a.experiment_id,
        experiment_b.experiment_id,
    }
    assert len(registry.all_results()) == 1


def test_find_by_tag() -> None:
    registry = ExperimentRegistry()
    tagged = make_test_experiment(name="Tagged", tags=["baseline"])
    untagged = make_test_experiment(name="Untagged", tags=[])
    registry.register(tagged)
    registry.register(untagged)

    found = registry.find_by_tag("baseline")

    assert [e.experiment_id for e in found] == [tagged.experiment_id]
