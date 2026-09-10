import importlib.util
from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_build_script():
    script_path = REPO_ROOT / "scripts" / "build.py"
    spec = importlib.util.spec_from_file_location("epicc_build_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stlite_requirements_exclude_kaleido() -> None:
    build_script = _load_build_script()

    config = build_script.load_config(REPO_ROOT / "pyproject.toml")
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)

    assert "plotly" in config["packages"]
    assert "kaleido" not in config["packages"]
    assert any(
        dependency.startswith("kaleido")
        for dependency in pyproject["project"]["dependencies"]
    )
