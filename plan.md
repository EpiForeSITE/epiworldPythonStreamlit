# Development plan

Based on the meeting of March 5th + the discussion on GitHub ([link](https://github.com/EpiForeSITE/epiworldPythonStreamlit/discussions/2)), here is a list of tasks/things that need to be built for the project.

## Example of yaml doc

From Olivia's comments:

```yaml
model:
  metadata:
    title: "Measles Outbreak Cost Calculator"
    description: "Estimates the economic cost of a measles outbreak across three outbreak-size scenarios."
    authors:
      - name: "Jane Doe"
        email: "jane@example.org"
      - name: "John Smith"
    introduction: |
      ## Background
      Measles is a highly contagious viral disease ...

      ## Assumptions
      All wage figures are in 2024 USD and are taken
      from the Bureau of Labor Statistics.

  parameters:
    cost_hosp:
      type: integer
      label: "Cost of measles hospitalization"
      description: "Average direct medical cost per hospitalised measles case (USD)."
      default: 31168
      min: 0
      max: 500000
      unit: "USD"
      references:
        - "Ortega-Sanchez et al. (2014). Vaccine, 32(34)."

    prop_hosp:
      type: number
      label: "Proportion of cases hospitalised"
      description: "Fraction of confirmed cases requiring hospital admission."
      default: 0.20
      min: 0
      max: 1
      unit: "proportion"
      references:
        - "CDC Measles surveillance data 2019."

  equations:
    eq_hosp:
      label: "Hospitalisation cost"
      unit: "USD"
      output: "integer"
      compute: "n_cases * prop_hosp * cost_hosp"

  table:
    scenarios:
      - id: "s_22"
        label: "22 Cases"
        vars:
          n_cases: 22
      - id: "s_100"
        label: "100 Cases"
        vars:
          n_cases: 100
      - id: "s_803"
        label: "803 Cases"
        vars:
          n_cases: 803

    rows:
      - label: "Hospitalisation cost"
        value: "eq_hosp"
      - label: "Lost productivity"
        value: "eq_lost_prod"
      - label: "Contact tracing cost"
        value: "eq_tracing"
      - label: "TOTAL"
        value: "eq_total"
        emphasis: "strong"

  figures:
    - title: "My figure"
      alt-text: "Some text"
      py-code: |
        import matplotlib as mp
        mp.plot(...)
```

## YAML document structure

The YAML document must define the following top-level sections:

- **Metadata:** Title, description, author(s), optional introduction text, and a Markdown report template with placeholders (e.g., `{{ table:table1 }}`, `{{ figure:fig1 }}`). An `assumptions` field (Markdown string) may also be included.
- **Parameters:** Named numeric parameters with type, label, description, default, min/max bounds, unit, and optional references.
- **Equations:** Named expressions (as safe Python arithmetic strings) with label, unit, and output type.
- **Tables:** Scenario columns (each defining a set of variable overrides) and rows (each pointing to an equation result).
- **Figures:** A list of figures, each with a title, alt-text, and a small Python snippet to generate the plot.
- **Current Parameters** *(optional):* A snapshot of parameter values representing the saved state of the model.

Example report template:

```md
# Title of the report

## Sub title

some text, some number {{ equation:value1 }}

{{ table:table1 }}

Some more text

{{ table:table2 }}

And a pretty figure

{{ figure:fig1 }}
```

## Tasks

### `validate_yaml(yaml_content: str) -> dict`

- **Input:** Raw YAML document as a string (e.g., file contents read from disk or uploaded by the user).
- **Output:** A validated Python dictionary representing the model, or raises a descriptive error on failure.
- **Steps:**
    1. Parse the YAML string into a dictionary. If not, then just check the dictionary. See the [SO reference on YAML validation in Python](https://stackoverflow.com/questions/3262569/validating-a-yaml-document-in-python/22231372#22231372) for schema-based approaches.
    2. Ensure that any embedded Python code (e.g., figure snippets) is not malicious. Use the [CPython AST module](https://docs.python.org/3/library/ast.html) (`ast.walk`) to inspect the parse tree, whitelist allowed node types/names, and reject anything outside that set.
    3. Check equations for recursive references and determine a safe execution order (topological sort).
    4. Validate units for consistency (e.g., ensure monetary values are not mixed with proportions without explicit conversion).

### `build_menu(model_dict: dict) -> None`

- **Input:** Validated model dictionary (output of `validate_yaml`).
- **Output:** No return value; renders the Streamlit sidebar/parameter panel with appropriate input widgets for each parameter.
- **Steps:**
    - Build input widgets from the `parameters` section.
    - Populate values using the `default` fields, unless `current_parameters` are present in the model dictionary (in which case those values take precedence).
    - Trigger guardrail warnings when parameter values approach `safe_min` / `safe_max` boundaries.

### `watch_parameters(model_dict: dict, current_values: dict) -> dict`

- **Input:** Validated model dictionary and a dictionary of current parameter values entered by the user.
- **Output:** A dictionary of validated parameter values, with warning messages attached for any values that fall outside `safe_min` / `safe_max` bounds.
- **Steps:**
    - For each parameter, check that its current value lies within `[safe_min, safe_max]`.
    - Return the validated values along with any triggered warnings.

### `run_model(model_dict: dict, parameters: dict) -> list[dict]`

- **Input:** Validated model dictionary and a validated parameter dictionary (output of `watch_parameters`).
- **Output:** A list of dictionaries, one per scenario column, where each dictionary maps equation/row names to computed numeric values.
- **Steps:**
    - Validate scenario ranges and column definitions.
    - For each scenario:
        1. Merge scenario-specific variable overrides into the base parameters.
        2. Evaluate equations in topologically-sorted order to produce row values.
    - Return the list of per-scenario result dictionaries.

### `generate_report(model_dict: dict, results: list[dict]) -> str`

- **Input:** Validated model dictionary and the list of scenario results (output of `run_model`).
- **Output:** An HTML string representing the full rendered report.
- **Steps:**
    - Process the Markdown report template, replacing `{{ equation:* }}`, `{{ table:* }}`, and `{{ figure:* }}` placeholders with computed values, formatted tables, and rendered figures respectively.
    - **Figures:** Consider using [Streamlit's built-in charting functions](https://docs.streamlit.io/develop/api-reference/charts) in preference to raw `matplotlib` calls, to simplify dependencies and keep the interface consistent with the Streamlit app.
    - Render the final document as an HTML string.

### `save_as_pdf(html_content: str) -> bytes`

- **Input:** HTML string (output of `generate_report`).
- **Output:** PDF file as bytes, ready to be offered as a download.
- **Notes:**
    - Since the app targets WASM (via `stlite`), dependencies that require native binaries (e.g., most headless-browser or Chromium-based libraries) are not available.
    - Potential approaches to evaluate:
        - Call a REST API service for HTML-to-PDF conversion.
        - Emit an intermediate TeX document and use a TeX-to-PDF pipeline where available.
        - Use browser-native APIs (e.g., `window.print()` / the `print` CSS media query) to trigger a client-side PDF save — this has been seen in production Streamlit apps and may be the most WASM-friendly option.
    - ReportLab and similar direct-to-PDF Python libraries may require paid licenses or native extensions; evaluate licensing before adopting.

### `store_model_state(model_dict: dict, parameters: dict) -> None`

- **Input:** Validated model dictionary and the current parameter values.
- **Output:** No return value; persists the model state so the user can navigate back to it.
- **Notes:**
    - `localStorage` (or `sessionStorage`) via Streamlit's JavaScript component API is the most likely mechanism in a WASM context, since there is no server-side filesystem. Investigate whether Streamlit exposes an API to this effect or whether a custom component is needed.
    - The UI could surface this as a small history panel or list of previously visited states.

### `save_current_model(model_dict: dict, current_parameters: dict) -> str`

- **Input:** Validated model dictionary and the current parameter values.
- **Output:** A YAML string (the original model with the `current_parameters` section populated) saved to disk or offered as a file download.
- **Steps:**
    - Merge the current parameter values into the model dictionary under `current_parameters`.
    - Serialise back to a YAML string.
    - Write to disk or trigger a browser download.

### Setup `stlite` framework

- Configure the project to run entirely in the browser using [`stlite`](https://stlite.net/).
- Verify that all dependencies (pure-Python or available as Pyodide wheels) are compatible with the WASM runtime.

## Other tasks (non-function)

These are project-level tasks that need to be addressed but do not map directly to a single function:

- **Branch protection rules:** Update the repository's branch protection rules to require all changes to be submitted via pull requests (no direct pushes to the main branch).
- **`AGENTS.md` file:** Draft a simple `AGENTS.md` file that describes the autonomous agents involved in the project, their roles, and the conventions they should follow.
- **GitHub Actions workflow — agent environment:** Create a GitHub Actions workflow that sets up the environment required by the agent (tools, credentials, runtime dependencies).
- **GitHub Actions workflow — CI testing:** Create a GitHub Actions workflow that installs project dependencies using [`uv`](https://github.com/astral-sh/uv) and runs the test suite on every push/PR.
- **Devcontainer environment:** Create a `.devcontainer` configuration (e.g., `devcontainer.json` + Dockerfile or feature list) so contributors can open the project in a fully configured, reproducible development container.

