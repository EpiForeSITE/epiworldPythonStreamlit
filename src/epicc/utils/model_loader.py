import os
import importlib.util
import sys

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


def load_model_from_file(filepath):
    """
    Loads a Python model file dynamically and returns the module object.
    The module must contain `run_model()` and `build_sections()`.
    """
    module_name = os.path.splitext(os.path.basename(filepath))[0]

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module
