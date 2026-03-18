"""
Configuration loading and schema management.

TODO: A lot of of this stuff is very restrictive, since the calculator was initially built to be
  deployed for handling one single model without being retargetable. In the future, we may want to
  make this more flexible, but for now, it's good enough.
"""

import importlib.resources
from epicc.formats import read_parameters
from typing import Any, Literal, cast
from pathlib import Path
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    title: str = Field(
        description="Display title of the application."
    )

    description: str = Field(
        description="Brief description of the application and its purpose."
    )


class DefaultsConfig(BaseModel):
    decimal_precision: int = Field(
        default=4,  # This used to be 28, not sure why, since that's very large.
        ge=1,
        le=16,
        description="Number of decimal places used in cost and probability calculations.",
    )

    ui_theme: Literal["light", "dark"] = Field(
        default="light",
        description="UI theme. One of 'light' or 'dark'.",
    )


class ModelPathsConfig(BaseModel):
    selected_path: Path = Field(
        description="Path to the directory containing built-in disease models."
    )

    custom_path: Path = Field(
        description="Path to the directory containing user-defined disease models."
    )


class Config(BaseModel):
    app: AppConfig
    defaults: DefaultsConfig
    model_paths: ModelPathsConfig


def load_config(name: str) -> tuple[Config, Any]:
    # We're okay to cast here because we know the file exists and Traversable is a supertype of
    # Path, but mypy doesn't know that.
    config_path = cast(Path, importlib.resources.files("epicc").joinpath(f"config/{name}.yaml"))    
    return read_parameters(config_path, config_path.open("rb"), Config)
    
CONFIG, _ = load_config("default")
