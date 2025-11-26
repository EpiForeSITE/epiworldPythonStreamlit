import yaml
import os

def load_model(model_file_path):
    """
    Loads <modelname>.yaml automatically.
    """
    base = os.path.dirname(model_file_path)
    name = os.path.basename(model_file_path).replace(".py", "")
    selected_path = os.path.join(base, f"{name}.yaml")

    if not os.path.exists(selected_path):
        return {}   # no defaults → model chooses own defaults

    with open(selected_path, "r") as f:
        return yaml.safe_load(f)
