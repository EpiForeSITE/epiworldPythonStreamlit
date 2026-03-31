import importlib.resources
from pathlib import Path
from typing import Any, cast

from epicc.formats import read_from_format
from epicc.model.schema import Model


def load_model(name: str) -> tuple[Model, Any]:
    # We're okay to cast here because we know the file exists and Traversable is a supertype of
    # Path, but mypy doesn't know that.
    config_path = cast(
        Path, importlib.resources.files("epicc").joinpath(f"models/{name}.yaml")
    )

    return read_from_format(config_path, config_path.open("rb"), Model)


__all__ = ["load_model"]
