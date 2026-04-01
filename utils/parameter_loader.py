from __future__ import annotations

import os
import yaml
import pandas as pd
from decimal import Decimal
import re
from typing import Any


def load_params_from_excel(excel_file):
    df = pd.read_excel(
        excel_file,
        usecols="F:H",
        header=1
    )

    df.columns = [str(c).strip().lower() for c in df.columns]

    if not {"parameter", "value"}.issubset(df.columns):
        raise ValueError("Expected columns Parameter and Value in F:G")

    params = {}
    for _, row in df.iterrows():
        if pd.isna(row["parameter"]) or pd.isna(row["value"]):
            continue

        cleaned = re.sub(r"[^0-9.\-]", "", str(row["value"]))
        if cleaned == "":
            continue

        params[str(row["parameter"]).strip()] = Decimal(cleaned)

    return params


def flatten_dict(d: dict[str, Any], level: int = 0) -> dict[str, Any]:
    """Flatten a nested dictionary for indented UI rendering."""
    flat: dict[str, Any] = {}
    for key, value in d.items():
        indented_key = ("\t" * level) + str(key)
        if isinstance(value, dict):
            flat[indented_key] = None
            flat.update(flatten_dict(value, level + 1))
        else:
            flat[indented_key] = value
    return flat


def get_leaf_defaults(flat_params: dict[str, Any]) -> dict[str, Any]:
    """Return editable leaf parameters with indentation removed."""
    cleaned: dict[str, Any] = {}
    for key, value in flat_params.items():
        if value is None:
            continue
        cleaned[str(key).lstrip("\t")] = value
    return cleaned


def load_model_params(model_file_path: str, uploaded_excel=None) -> dict[str, Any]:
    """Load model parameters from Excel or the paired YAML file."""
    if uploaded_excel is not None:
        return load_params_from_excel(uploaded_excel)

    base = os.path.dirname(model_file_path)
    name = os.path.basename(model_file_path).replace(".py", "")
    yaml_path = os.path.join(base, f"{name}.yaml")

    if not os.path.exists(yaml_path):
        return {}

    with open(yaml_path, "r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    if isinstance(raw, dict) and isinstance(raw.get("parameters"), dict):
        raw = raw["parameters"]

    if not isinstance(raw, dict):
        return {}

    flat = flatten_dict(raw)
    return get_leaf_defaults(flat)
