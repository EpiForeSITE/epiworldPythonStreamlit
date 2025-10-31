import importlib

def load_model(model_id: str):
    """
    Dynamically load a model using its full module path.
    The module must have a `run_model(params)` function.   Example: 'models.tb_isolation'
    """
    try:
        module = importlib.import_module(model_id)
        if hasattr(module, "run_model"):
            return module.run_model
        raise AttributeError(f"'{model_id}' has no 'run_model(params)' function.")
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Model '{model_id}' not found. "
            f"Ensure {model_id.replace('.', '/') + '.py'} exists."
        ) from e
