"""Tests for epicc.model (load_model)."""

import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from epicc.model import load_model
from epicc.model.schema import Model

_VALID_MODEL_YAML = textwrap.dedent("""\
    metadata:
      title: Test Model
      description: A minimal test model.
    parameters:
      rate:
        type: number
        label: Rate
        default: 0.5
    equations:
      total:
        label: Total
        compute: "rate * 100"
    table:
      scenarios: []
      rows: []
""")


@pytest.fixture
def valid_model_path():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(_VALID_MODEL_YAML)
        path = Path(f.name)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# load_model: patched to avoid relying on built-in model file format
# ---------------------------------------------------------------------------


def test_load_model_returns_model_and_template(valid_model_path: Path):
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = valid_model_path
        model, template = load_model("my_model")

    assert isinstance(model, Model)
    assert model.metadata.title == "Test Model"
    assert "rate" in model.parameters
    assert "total" in model.equations


def test_load_model_has_parameters(valid_model_path: Path):
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = valid_model_path
        model, _ = load_model("my_model")

    assert len(model.parameters) > 0


def test_load_model_parameter_fields(valid_model_path: Path):
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = valid_model_path
        model, _ = load_model("my_model")

    rate = model.parameters["rate"]
    assert rate.type == "number"
    assert rate.default == 0.5


def test_load_model_equations(valid_model_path: Path):
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = valid_model_path
        model, _ = load_model("my_model")

    assert model.equations["total"].compute == "rate * 100"


def test_load_model_nonexistent_file_raises():
    with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
        missing = Path(f.name + ".gone")
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = missing
        with pytest.raises(Exception):
            load_model("does_not_exist")


def test_load_model_invalid_schema_raises():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("just: a flat file\nwith: no structure\n")
        bad_path = Path(f.name)
    with patch("epicc.model.importlib.resources") as mock_res:
        mock_res.files.return_value.joinpath.return_value = bad_path
        with pytest.raises(ValueError, match="Data validation failed"):
            load_model("bad_model")
