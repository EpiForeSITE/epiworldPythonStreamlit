import os
import yaml
import pandas as pd
from decimal import Decimal
import re


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


def flatten_dict(d, level=0):
    flat = {}
    for key, value in d.items():
        indented_key = ("\t" * level) + str(key)

        if isinstance(value, dict):
            flat[indented_key] = None
            flat.update(flatten_dict(value, level + 1))
        else:
            flat[indented_key] = value
    return flat


def load_model_params(model_file_path, uploaded_excel=None):
    if uploaded_excel:
        return load_params_from_excel(uploaded_excel)

    base = os.path.dirname(model_file_path)
    name = os.path.basename(model_file_path).replace(".py", "")
    yaml_path = os.path.join(base, f"{name}.yaml")

    if not os.path.exists(yaml_path):
        return {}

    with open(yaml_path, "r") as f:
        raw = yaml.safe_load(f) or {}

    return flatten_dict(raw)
