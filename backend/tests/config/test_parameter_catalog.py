from pathlib import Path

from app.config.parameter_catalog import PARAMETER_CATALOG

_DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "PARAMETER_CATALOG.md"


def test_catalog_is_not_empty() -> None:
    assert len(PARAMETER_CATALOG) > 0


def test_every_catalog_entry_has_all_fields_populated() -> None:
    for entry in PARAMETER_CATALOG:
        assert entry.name
        assert entry.description
        assert entry.data_type
        assert entry.default_value != ""
        assert entry.allowed_range
        assert entry.owning_module
        assert entry.safe_to_optimize in {"Yes", "No", "N/A"}
        assert entry.reason


def test_no_duplicate_parameter_names() -> None:
    names = [entry.name for entry in PARAMETER_CATALOG]
    assert len(names) == len(set(names))


def test_every_catalog_entry_is_documented_in_the_markdown_catalog() -> None:
    doc_text = _DOC_PATH.read_text()

    missing = [entry.name for entry in PARAMETER_CATALOG if entry.name not in doc_text]

    assert not missing, f"Parameters missing from docs/PARAMETER_CATALOG.md: {missing}"
