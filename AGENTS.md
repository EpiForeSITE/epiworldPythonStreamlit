# AGENTS.md — EpiCON Cost Calculator

This file describes the conventions, roles, and constraints for contributors working in this
repository. All agents — whether running in GitHub Actions or invoked interactively — should
read and follow this document before making changes.

---

## Project overview

**EpiCON** is a browser-based epidemiological cost calculator built with **Streamlit** and
distributed as a static **stlite** build for browser execution.

The current app supports two model flows:

1. **Python + YAML models**
   - A Python module in `models/` implements model logic.
   - A paired YAML file provides default parameters.
   - `app.py` loads the Python module, loads YAML defaults, renders parameter inputs,
     runs the model, and renders sections.

2. **Excel-driven models**
   - An uploaded `.xlsx` file is parsed by `utils/excel_model_runner.py`.
   - Parameters and computed outputs are rendered from workbook contents.

Current high-level flow:

`discover_models() → load_model_from_file() / load_model_params() → render_parameters_with_indent() → run_model() → build_sections() → render_sections()`

Persistence helpers:
- `store_model_state()`
- `save_current_model()`

---

## Repository layout

```text
epiworldPythonStreamlit/
├── app.py
├── models/                 # Python model modules + paired YAML parameter files
├── utils/
│   ├── model_loader.py
│   ├── parameter_loader.py
│   ├── parameter_ui.py
│   ├── excel_model_runner.py
│   └── section_renderer.py
├── config/
├── styles/
├── scripts/                # stlite build helpers
├── build/                  # generated static output
├── docs/
├── pyproject.toml
├── Makefile
├── AGENTS.md
└── README.md
```

---

## Coding conventions

All agent-generated code must follow these standards.

### Style
- Follow **PEP 8** for all Python code.
- Use **type hints** on every function signature.
- Write **docstrings** for every public function and class.
- Maximum line length: **100 characters**.

### Testing
- Tests use **pytest** only.
- Add or update pytest coverage for every changed public function whenever a `tests/` target
  exists for that module.
- Prefer pure-Python tests compatible with the stlite/Pyodide target.
- Avoid test dependencies that require native binaries.
- Aim for at least **80% line coverage** on new code where CI coverage is enforced.

### Dependencies
- Add dependencies via `pyproject.toml` only, managed by `uv`.
- Runtime dependencies must be **pure-Python** or available as **Pyodide wheels**.
- Dev-only dependencies are exempt from the Pyodide runtime constraint.

### Security
- Equations and figure code in YAML files are untrusted input.
- Validate them with the CPython `ast` module before evaluation.
- Never use `eval()` or `exec()` on unvalidated user-supplied strings.
- Do not log or print parameter values that could contain PII.

### Git workflow
- **No direct pushes to `main`.**
- Use branch names like:
  - `feat/<short-description>`
  - `fix/<short-description>`
  - `chore/<short-description>`
- Use **Conventional Commits** for commit messages.
- Each PR should address a single concern.

---

## Function contracts (current)

Agents must not change a function signature or return type without updating all callers and
tests.

### App / utility layer
- `discover_models(path: str) -> dict[str, str]`
- `load_model_from_file(filepath: str) -> object`
- `load_model_params(model_file_path: str, uploaded_excel=None) -> dict`
- `flatten_dict(d, level=0)`
- `render_parameters_with_indent(param_dict, params, label_overrides) -> None`
- `reset_parameters_to_defaults(param_dict, params, model_id) -> None`
- `render_sections(sections) -> None`

### Python model modules
Each Python model module in `models/` must expose:
- `model_title: str`
- `model_description: str`
- `run_model(params: dict, label_overrides: dict | None = None) -> list[dict]`
- `build_sections(results: list[dict]) -> list[dict]`

---

## Agent roles

### Interactive development agents
**Scope:** Code generation, refactoring, documentation, tests, YAML schema work, and code
review suggestions.

**Constraints:**
- Always read `AGENTS.md` and relevant source files before proposing changes.
- Do not modify `pyproject.toml` dependencies without explaining Pyodide compatibility.
- Use AST validation for equation evaluation.
- Prefer Streamlit-native rendering over heavier plotting dependencies.
- For browser-only persistence, use browser storage patterns rather than server-side files.
- Propose tests alongside implementation changes.

### GitHub Actions — CI agent
**Trigger:** Every push and every PR targeting `main`.

**Expected steps:**
1. Check out the repository.
2. Install dependencies with `uv`.
3. Run `ruff`.
4. Run `mypy`.
5. Run `pytest` with coverage.
6. Fail if configured coverage thresholds are not met.

**Constraints:**
- Must run in the project’s supported development environment.
- Do not upload artifacts unless explicitly configured.

### GitHub Actions — agent environment
**Purpose:** Set up credentials, tools, and optional external service tokens.

**Constraints:**
- Secrets must be stored in GitHub Actions Secrets.
- Fail loudly if required secrets are missing.

---

## YAML model schema

The app currently supports both of these YAML layouts.

### 1. Flat key/value defaults
```yaml
Cost of measles hospitalization: 31168
Proportion of cases hospitalized: 0.2
```

### 2. Nested parameter dictionary
```yaml
parameters:
  Cost of measles hospitalization: 31168
  Proportion of cases hospitalized: 0.2
```

Agents must preserve compatibility with both layouts unless the app is explicitly migrated.

### Reference schema for future structured models
```yaml
model:
  metadata:
  parameters:
  equations:
  table:
  figures:
  current_parameters:
```

If generating new structured YAML, keep it compatible with current loaders or update the
loaders and tests together.

---

## Out-of-scope for agents

The following are off-limits without explicit human approval in PR review:

- Changing branch protection rules.
- Adding `eval()` or `exec()` on user-supplied strings.
- Introducing runtime dependencies that require native binaries.
- Modifying the public function signatures listed above.
- Writing outside the repository working directory.
- Disabling or skipping CI checks.

---

## Getting started

```bash
uv sync
make dev
make setup
make serve
make check
```

For architecture questions, refer to the development plan, inline source comments, and current
utility/model implementations.