import os
import importlib.util

def discover_models(path):
    """Return {model_name: file_path} for Python model files."""
    if not os.path.isdir(path):
        return {}
    models = {}
    for f in os.listdir(path):
        if f.endswith(".py") and not f.startswith("__"):
            name = f[:-3]
            models[name] = os.path.join(path, f)
    return models


def load_model_from_file(path):
    """Import a Python model file dynamically and return its run_model() function."""
    module_name = os.path.splitext(os.path.basename(path))[0]

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "run_model"):
        raise ValueError(f"Model file '{module_name}' must define run_model(params).")

    return module.run_model
