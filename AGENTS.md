# AGENTS.md — EpiCON Cost Calculator

This file describes the conventions, roles when contributing to this repository. All agents — whether running in a GitHub Actions environment or invoked interactively — should read and respect this document before making any changes.

---

## Project overview

**EpiCON** is a browser-based epidemiological cost calculator built on [stlite](https://stlite.net/) (Streamlit compiled to WebAssembly). Users load a YAML model file, adjust parameters through an auto-generated UI, and receive a formatted HTML/PDF report of scenario costs.

The core pipeline is:

```
validate_yaml() → build_menu() → watch_parameters() → run_model() → generate_report() → save_as_pdf()
```

Persistence helpers: `store_model_state()`, `save_current_model()`

---

## Repository layout

```
epiworldPythonStreamlit/
├── .devcontainer/          # Reproducible dev environment (future)
├── .github/
│   └── workflows/
│       ├── ci.yml          # CI: install (uv) + run tests on every push/PR
│       └── agent.yml       # Agent environment setup (future)
├── utils/
│   ├── model_loader.py     # validate_yaml()
│   ├── parameter_ui.py     # build_menu(), watch_parameters()
│   ├── excel_model_runner.py # run_model()
│   ├── section_renderer.py # generate_report()
│   └── ...                 # save_as_pdf(), store_model_state(), save_current_model()
├── models/
│   └── measles_outbreak.yaml # Reference YAML model
├── config/
├── styles/
├── scripts/
├── build/
├── tests/                  # (future)
├── app.py                  # Streamlit entry point
├── pyproject.toml
├── AGENTS.md
├── Makefile
├── README.md
└── plan.md
```

---

## Coding conventions

All agent-generated code must conform to the following standards. Pull requests that violate these will be rejected by CI.

### Style
- Follow **PEP 8** for all Python code.
- Use **type hints** on every function signature (parameters and return type).
- Write **docstrings** for every public function and class (Google-style preferred).
- Maximum line length: **100 characters**.

### Testing
- Every public function must have at least one corresponding test in `tests/`.
- Tests use **pytest**. Do not introduce other test frameworks.
- Aim for ≥ 80 % line coverage on new code.
- Tests must pass in the WASM-compatible environment — avoid test dependencies that require native binaries.

### Dependencies
- Add dependencies via `pyproject.toml` only (managed by [`uv`](https://github.com/astral-sh/uv)).
- All runtime dependencies must be **pure-Python** or available as **Pyodide wheels**, since the app targets WASM via stlite. Validate any new dependency against the [Pyodide package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) before adding it.
- Dev-only dependencies (linters, test tools) are exempt from the Pyodide constraint.

### Security
- Equations and figure code in YAML files are untrusted user input. Always validate them with the **CPython `ast` module** (`ast.walk` whitelist) before evaluation. Never use `eval()` or `exec()` on unvalidated strings.
- Do not log or print parameter values that could contain PII.

### Git workflow
- **No direct pushes to `main`.** All changes must go through a pull request.
- Branch names should follow: `feat/<short-description>`, `fix/<short-description>`, or `chore/<short-description>`.
- Commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/) spec (e.g., `feat: add watch_parameters validation`).
- Each PR should address a single concern; avoid bundling unrelated changes.

---

## Function contracts (do not break these)

Agents must not change a function's signature or return type without updating all callers and tests. The authoritative signatures are:

| Function | Signature |
|---|---|
| `validate_yaml` | `(yaml_content: str) -> dict` |
| `build_menu` | `(model_dict: dict) -> None` |
| `watch_parameters` | `(model_dict: dict, current_values: dict) -> dict` |
| `run_model` | `(model_dict: dict, parameters: dict) -> list[dict]` |
| `generate_report` | `(model_dict: dict, results: list[dict]) -> str` |
| `save_as_pdf` | `(html_content: str) -> bytes` |
| `store_model_state` | `(model_dict: dict, parameters: dict) -> None` |
| `save_current_model` | `(model_dict: dict, current_parameters: dict) -> str` |

---

## Agent roles

### Claude (Anthropic) — interactive development agent

**Scope:** Code generation, refactoring, documentation, test writing, YAML schema design, and code review suggestions.

**Constraints:**
- Always read `AGENTS.md` and the relevant source file(s) before proposing changes.
- Do not modify `pyproject.toml` dependencies without explaining the Pyodide compatibility status of any new package.
- When implementing equation evaluation, use the AST whitelist pattern — never raw `eval()`.
- When generating figure code, prefer Streamlit's native charting API over raw `matplotlib` to keep the WASM dependency surface small.
- For `save_as_pdf`, do not introduce Chromium/headless-browser dependencies. Prefer `window.print()` / print-CSS or a REST API approach.
- For `store_model_state`, use `localStorage`/`sessionStorage` via Streamlit's JS component API (no server-side filesystem in WASM).
- Propose tests alongside any new implementation code.
- Follow the branch/commit conventions above when creating files or suggesting git commands.

### GitHub Actions — CI agent (`ci.yml`)

**Trigger:** Every push and every pull request targeting `main`.

**Steps:**
1. Check out the repository.
2. Install Python and dependencies using `uv`.
3. Run `ruff` (linting) and `mypy` (type checking).
4. Run the full `pytest` suite with coverage reporting.
5. Fail the workflow if coverage on new lines drops below 80 %.

**Constraints:**
- Must run in the same devcontainer-compatible base image used in `.devcontainer/`.
- Do not upload build artifacts unless explicitly configured to do so.

### GitHub Actions — agent environment (`agent.yml`)

**Trigger:** Manual dispatch or on-schedule, as configured.

**Purpose:** Sets up credentials, runtime tools, and any external service tokens needed by autonomous agents (e.g., API keys for PDF conversion services).

**Constraints:**
- Secrets must be stored in GitHub Actions Secrets — never hard-coded in workflow files or source code.
- The workflow must fail loudly (non-zero exit) if a required secret is missing rather than continuing silently.

---

## YAML model schema (reference)

When validating or generating YAML files, agents must enforce this top-level structure:

```
model:
  metadata:      # required — title, description, authors, introduction
  parameters:    # required — named numeric parameters with type, default, min, max
  equations:     # required — named safe Python arithmetic expressions
  table:         # required — scenario columns and row definitions
  figures:       # optional — list of titled figures with Python plot snippets
  current_parameters:  # optional — saved parameter snapshot
```

See `models/measles_outbreak.yaml` for a complete, annotated reference document.

---

## Out-of-scope for agents

The following are explicitly off-limits without explicit human approval in a PR review:

- Changing branch protection rules.
- Adding `eval()` / `exec()` calls on user-supplied strings.
- Introducing dependencies that require native binaries at runtime.
- Modifying the public function signatures listed above.
- Writing to any path outside the repository working directory.
- Disabling or skipping CI checks.

---

## Getting started (for humans and agents alike)

```bash
# Open in devcontainer (recommended)
code .   # VS Code will prompt to reopen in container

# Or install locally with uv
uv sync
uv run pytest
uv run streamlit run app.py
```

For questions about the project architecture, see the discussion thread linked in the development plan and the inline comments in each source module.