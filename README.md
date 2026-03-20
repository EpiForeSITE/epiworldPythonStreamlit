# epiworldPythonStreamlit

Streamlit webapp for epiworld.

Please install dependencies with a dependency manager capable of reading `pyproject.toml` files
(most modern solutions will work). For example, with [`uv`](https://docs.astral.sh/uv/):

```
uv sync
```

Please note that this step is not required if working in a containerized context.

You may then run with:

```
uv run -m streamlit run app.py
```

## Launch the App online

Click below to open the live Streamlit application, as currently deployed:

https://epiworldpythonapp.streamlit.app/

*(If the app is still deploying, it may take a few seconds to load.)*

Please follow instructions in your console for loading development versions.

## Modeling systems

The application supports two active modeling approaches:

- **Built-in Python models** — `.py` files in `models/`, each paired with a `.yaml` file of
  default parameter values. Calculation logic is written in Python.
- **Excel-driven models** — `.xlsx` workbooks uploaded at runtime. Parameters live in columns F–G
  of the spreadsheet; calculation logic lives in Excel formulas, which the app evaluates using a
  built-in formula engine.

A third approach — a standalone **YAML model spec** that defines parameters, equations, scenarios,
and report templates in a single file — is planned and described in `plan.md`.

See [docs/architecture.md](docs/architecture.md) for a detailed comparison of all three systems,
an explanation of the two different roles YAML plays in the codebase, and possible paths for
consolidating the approaches.
