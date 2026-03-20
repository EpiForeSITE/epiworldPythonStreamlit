# Architecture: Modeling Systems

This document explains the three modeling systems used in this application, how they relate to one another, and how they might be consolidated going forward.

---

## Overview

The application currently supports two active modeling approaches and one planned future approach:

| System | Where logic lives | How parameters are defined | Status |
|---|---|---|---|
| **Built-in Python models** | Python code (`.py`) | Companion YAML file | Active |
| **Excel-driven models** | Excel formulas | Columns F–G of spreadsheet | Active |
| **YAML model spec** | YAML equations | YAML `parameters` section | Planned |

---

## System 1 — Built-in Python Models

Built-in models are Python files placed in the `models/` directory. Each model file is paired with a YAML file of the same name that holds the default parameter values.

```
models/
├── measles_outbreak.py     # Calculation logic
├── measles_outbreak.yaml   # Default parameter values
├── tb_isolation.py
└── tb_isolation.yaml
```

### How they work

1. `utils/model_loader.py` scans `models/` for `.py` files at startup.
2. The user picks a model from the dropdown and sees its parameters in the sidebar.
3. Default parameter values come from the companion `.yaml` file, loaded by `utils/parameter_loader.py`.
4. The user can optionally override defaults by uploading their own `.yaml` or `.xlsx` parameter file.
5. When "Run Simulation" is clicked, `app.py` calls `model_module.run_model(params)`, which returns a results dictionary.
6. `model_module.build_sections(results)` converts the dictionary into a list of sections (tables, text) for display.

### What a model file must define

```python
model_title = "Human-readable title"
model_description = "Short description shown below the title."

SCENARIO_LABELS = {          # optional — keys are internal IDs, values are column headers
    "scenario_key": "Column Label",
}

def run_model(params: dict, label_overrides: dict = None) -> dict:
    """Perform calculations. Return a dict of DataFrames/values."""
    ...

def build_sections(results: dict) -> list[dict]:
    """Convert results dict into sections for the renderer."""
    ...
```

### What the companion YAML holds

The YAML file is a flat or one-level-nested mapping of parameter labels to default values:

```yaml
Cost of measles hospitalization: 31168
Proportion of cases hospitalized: 0.2
Hourly wage for worker: 29.36

Costs:                              # nested group — rendered as a collapsible expander
  Cost of latent TB infection: 300
  Cost of active TB infection: 34523
```

The `utils/parameter_loader.py::flatten_dict()` function converts nested YAML into a flat dictionary whose keys are tab-indented strings. `utils/parameter_ui.py` uses the indentation level to decide whether to render a plain sidebar input or a collapsible expander group.

### Pros and cons

**Pros**
- Full Python expressiveness: arbitrary calculations, loops, library calls.
- Precise numeric control (the models use `decimal.Decimal` for rounding accuracy).
- Easy to version-control and code-review.

**Cons**
- Adding a new model requires writing Python code.
- Calculation logic is not visible to non-programmers.
- Parameters and calculations are spread across two files (`.py` + `.yaml`).

---

## System 2 — Excel-Driven Models

The Excel-driven system lets a user upload any `.xlsx` workbook and have the application treat it as a runnable model. No Python code is written for the model itself; the calculation logic lives entirely in Excel formulas.

### Expected spreadsheet layout

The system expects a specific cell layout within the uploaded workbook:

```
Column A  — Outcome row labels (results section)
Columns B–E — Scenario values (results and inputs per scenario)
Column F  — Parameter name
Column G  — Parameter value or formula
Row 1     — (ignored)
Row 2     — Column headers
Rows 3+   — Parameter rows (F:G) and scenario input rows (B:E)
```

The **results (outcome) section** starts wherever the first non-empty cell in column A appears. Each row in that section corresponds to one output metric displayed in the final table.

### How it works

1. The user selects **Excel Driven Model** from the model dropdown and uploads a `.xlsx` file.
2. `utils/excel_model_runner.py::load_excel_params_defaults_with_computed()` reads parameter names and default values from columns F–G (starting at row 3).
3. The user edits parameter values in the sidebar; column B–E headers can also be renamed.
4. On "Run Simulation", `run_excel_driven_model()`:
   a. Writes the user's parameter values back into columns F–G of an in-memory workbook copy.
   b. Evaluates all Excel formulas in the outcome section using the built-in `FormulaEngine`.
   c. Returns a sections dictionary in the same format as built-in models.
5. The same `utils/section_renderer.py::render_sections()` function displays the results.

### The formula engine

Because Python's `openpyxl` library does not evaluate formulas, `excel_model_runner.py` includes a custom `FormulaEngine` class that:

- Reads a formula string such as `=G3*G4*G5`.
- Translates Excel cell references (`G3`) and range references (`G3:G10`) into Python expressions.
- Uses `ast.walk` to whitelist allowed expression nodes before calling `eval`, preventing arbitrary code execution.
- Supports a set of Excel functions: `SUM`, `MIN`, `MAX`, `IF`, `SUMPRODUCT`, `INDIRECT`, `ROW`, `RANGE`.

### Example Excel files

Two example workbooks are included in the repository root:

- `Measles Outbreak.xlsx` — spreadsheet encoding of the measles model
- `TB Isolation.xlsx` — spreadsheet encoding of the TB isolation model

These implement exactly the same calculations as their Python counterparts, allowing side-by-side comparison of the two approaches.

### Pros and cons

**Pros**
- No programming required — subject-matter experts can build models in Excel.
- Existing spreadsheet models can be uploaded directly.
- Scenario columns and outcome rows are fully configurable in the spreadsheet.

**Cons**
- The formula engine re-implements a subset of Excel; complex or unusual formulas may not evaluate correctly.
- Debugging is harder — formula errors appear only at runtime.
- The spreadsheet must follow a specific column layout; deviations break parameter loading.
- Excel files are difficult to diff and code-review.

---

## System 3 — Planned YAML Model Spec (not yet implemented)

`plan.md` describes a third, more structured system in which a single YAML document fully specifies a model: its metadata, parameters (with types, bounds, and units), equations (as safe Python arithmetic strings), scenario tables, and optional figures and report templates.

### Example structure

```yaml
model:
  metadata:
    title: "Measles Outbreak Cost Calculator"
    description: "Estimates the economic cost of a measles outbreak."
    authors:
      - name: "Jane Doe"

  parameters:
    cost_hosp:
      type: integer
      label: "Cost of measles hospitalization"
      default: 31168
      min: 0
      max: 500000
      unit: "USD"

  equations:
    eq_hosp:
      label: "Hospitalisation cost"
      unit: "USD"
      compute: "n_cases * prop_hosp * cost_hosp"

  table:
    scenarios:
      - id: "s_22"
        label: "22 Cases"
        vars:
          n_cases: 22
    rows:
      - label: "Hospitalisation cost"
        value: "eq_hosp"

  figures:
    - title: "Cost breakdown"
      py-code: |
        import matplotlib.pyplot as plt
        plt.bar(...)
```

### Key planned functions

| Function | Purpose |
|---|---|
| `validate_yaml(yaml_content)` | Parse YAML, check schema, safety-check embedded code with `ast.walk` |
| `build_menu(model_dict)` | Render sidebar widgets from the `parameters` section |
| `watch_parameters(model_dict, values)` | Check values against `min`/`max` bounds, return warnings |
| `run_model(model_dict, parameters)` | Evaluate equations in dependency order, one result per scenario |
| `generate_report(model_dict, results)` | Fill a Markdown template and render to HTML |
| `save_current_model(model_dict, params)` | Serialize model + current values back to YAML for download |

See `plan.md` for full details and the task dependency diagram.

---

## The Two Roles of YAML

YAML is used in two distinct ways in this codebase, which can cause confusion:

### Role 1 — Parameter defaults (current, simple)

The `.yaml` files alongside Python model files (`models/*.yaml`) are **plain key-value stores**. They only hold default parameter values and have no structure beyond flat keys and one level of nesting for grouping. They are loaded by `utils/parameter_loader.py` and presented as editable sidebar inputs.

```yaml
# models/measles_outbreak.yaml — only default values, no schema
Cost of measles hospitalization: 31168
Proportion of cases hospitalized: 0.2
```

### Role 2 — Full model specification (planned)

The planned YAML system (Role 2) is a **complete model definition language**. A single YAML file would replace both the Python model file *and* its companion YAML parameter file. It defines parameter types, bounds, units, equations, scenarios, and report templates.

These two roles are currently handled by completely separate code paths and file formats. The planned YAML spec (Role 2) would eventually absorb Role 1 as its `parameters` and `current_parameters` sections.

---

## How the Systems Compare

| Concern | Python + YAML | Excel-driven | Planned YAML spec |
|---|---|---|---|
| **Who authors the model** | Developer | Analyst (spreadsheet) | Either |
| **Calculation logic** | Python code | Excel formulas | YAML `compute` strings |
| **Parameter definitions** | Companion `.yaml` (values only) | Columns F–G of workbook | `parameters` section (type, bounds, unit) |
| **Scenario definitions** | Hardcoded in Python | Columns B–E of workbook | `table.scenarios` section |
| **Input validation** | Ad hoc, in Python | None | `min`/`max` bounds + `watch_parameters` |
| **Report / export** | None | None | Markdown template → HTML → PDF |
| **Version control friendly** | Yes | No | Yes |
| **Formula debugging** | Python tracebacks | Runtime errors only | Python tracebacks |
| **Complexity** | Medium | Low (author), High (engine) | Low (author), Medium (engine) |

---

## Possible Consolidation Paths

The three systems overlap significantly. Below are the main strategies for reducing that overlap.

### Option A — YAML spec subsumes both (recommended long term)

Once the YAML model spec is implemented (see `plan.md`), built-in Python models can be migrated to YAML files in the same `models/` directory. The discovery logic in `utils/model_loader.py` would be extended to detect `.yaml` model files alongside `.py` ones.

Excel models can be migrated to YAML with a one-time conversion: the parameter table (columns F–G) maps directly to `parameters` entries, and the outcome formulas can be transcribed as `equations`.

This path would eventually yield a single model-running code path in `app.py` instead of the current two (`if selected_model_file == "__EXCEL_DRIVEN__": ... else: ...`).

### Option B — Excel as a YAML authoring tool

Rather than running Excel formulas at runtime, the app could treat an uploaded Excel file as a *source* for generating a YAML model spec. A conversion step would extract parameters, formulas, and outcome rows from the workbook and emit a `.yaml` file that the user can download, inspect, and use as the canonical model definition. Subsequent runs would use the YAML file, not the workbook.

This keeps the Excel-driven authoring experience while removing the need for the runtime formula engine.

### Option C — Minimal consolidation: shared rendering pipeline

As a near-term improvement that requires no new features, the two active code paths in `app.py` could be unified. Both paths load parameters, render sidebar widgets, run a model, and call `render_sections()`. The branching currently happens at several points (parameter loading, reset callback, label loading, run). Extracting a common `ModelRunner` abstraction that wraps both Python and Excel models behind the same interface would reduce duplication without changing any user-visible behaviour.

---

## Adding a New Model Today

### Built-in Python model

1. Create `models/my_model.py` implementing `run_model(params, label_overrides=None)` and `build_sections(results)`.
2. Create `models/my_model.yaml` with default parameter values.
3. The model appears automatically in the dropdown on next app start.

### Excel-driven model

1. Prepare a `.xlsx` workbook with parameters in columns F–G (rows 3+) and outcome formulas referencing those cells.
2. Place scenario headers in row 2, columns B–E.
3. Upload the file using the **Excel Driven Model** option in the sidebar.

See the included `Measles Outbreak.xlsx` and `TB Isolation.xlsx` for concrete examples of both built-in models reimplemented as Excel workbooks.
