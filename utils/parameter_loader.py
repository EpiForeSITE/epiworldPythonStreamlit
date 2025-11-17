import yaml
import os

def load_model_defaults(model_file_path):
    """
    Loads <modelname>_defaults.yaml automatically.
    """
    base = os.path.dirname(model_file_path)
    name = os.path.basename(model_file_path).replace(".py", "")
    defaults_path = os.path.join(base, f"{name}_defaults.yaml")

    if not os.path.exists(defaults_path):
        return {}   # no defaults → model chooses own defaults

    with open(defaults_path, "r") as f:
        return yaml.safe_load(f)
