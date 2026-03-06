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

## Tasks 

- Define what the structure is
    - Metadata
        - Title of the model
        - Description
        - Author of the model
        - Report structure (markdown with some placeholders). These placeholders would be automatically replaced when rendering the report (For instance `{{ table:table1 }}`).

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
        - Assumptions (another markdown document)
    - Paramteres
    - Equations
    - Tables
    - Current Parameters (in the case that the user wants to save the current state of the model.)
    - A way to describe what defines a column, for instance, a column could be number of cases, number of days of isolation.

- Function to validate the yaml file:
    1. Validate the yaml file (need to write a yaml schema + validator?). If not, then just check the dictionary.
    2. Ensure that the Python code is not malicious.
    3. Eq. validation also checks for recursive calls of values + the right order of execution.
    4. Validate the units (for instance, money or whatever)

- Function to generate the menu with the options from the yaml
    - Build the menu based on the parameters.
    - Populate the values using the defauls, unless the `current_parameters` are in the model file.
    - This should trigger the warnings associated with the guardrails.

- Function to watch the iteractivity with the model parameters:
    - Essentially to check the boundaries of `safe_min` and `safe_max` when the user makes changes.

- Function to run the model.
    - Validate the ranges/breaks (how many cases.). Then for each case do:
        1. Compute the equations (for which you need to ensure that you are doing the proper order) -> generate values for the table
        2. This returns the tables as dictionaries.
    - This returns a list of dictionaries (the columns for the table)

- Function to generate the report
    - Write/process the markdown document (mostly the text attached to the yaml).
    - Write the tables resulting from the calculations (inserting them into the `{{}}` placeholders).
    - Generate the figures, also base on placeholders `{{}}`
    - Render the report as an HTML file.

- Function to save as a pdf.

- Functionality to temporarily store the models, so the user can go back.
    - Could be a little window or list that shows some history or related.

- Function to save the current model:
    - Take the current yaml file.
    - Attach the current parameters.
    - Save it as a yml file to the disk.

- Setup the framework for running on the browser with [`stlite`](https://stlite.net/)

