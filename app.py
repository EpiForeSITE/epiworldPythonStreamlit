import os
import yaml
import streamlit as st
import inspect

from utils.model_loader import discover_models, load_model_from_file
from utils.parameter_loader import load_model_params, flatten_dict
from utils.section_renderer import render_sections
from utils.parameter_ui import render_parameters_with_indent, reset_parameters_to_defaults
from utils.excel_model_runner import (
    load_excel_params_defaults_with_computed,
    run_excel_driven_model,
    get_scenario_headers
)

# DIRECTORY & CONFIG
base_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base_dir, "config/app.yaml")) as f:
    app_config = yaml.safe_load(f)

with open(os.path.join(base_dir, "config/paths.yaml")) as f:
    path_config = yaml.safe_load(f)


# UI STYLES
def load_css(file_path: str):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css(os.path.join(base_dir, "styles/sidebar.css"))

# MODEL SELECTION
st.sidebar.header("Simulation Controls")

selected_path = os.path.join(base_dir, path_config["model_paths"]["selected_path"])
default_custom_path = os.path.join(base_dir, path_config["model_paths"]["custom_path"])

user_custom_path = st.sidebar.text_input(
    "Custom Models Folder",
    value=default_custom_path
)

selected_models = discover_models(selected_path)
custom_models = discover_models(user_custom_path)

model_options = {}
model_options["Excel Driven Model"] = "__EXCEL_DRIVEN__"
model_options.update({name: file for name, file in selected_models.items()})
model_options.update({f"Custom: {name}": file for name, file in custom_models.items()})

if not model_options:
    st.sidebar.warning("No valid model files found.")
    st.stop()

selected_label = st.sidebar.selectbox(
    "Select Model",
    list(model_options.keys())
)

selected_model_file = model_options[selected_label]

# MODEL CHANGE RESET
model_key = (
    "__EXCEL_DRIVEN__"
    if selected_model_file == "__EXCEL_DRIVEN__"
    else os.path.basename(selected_model_file)
)

if "active_model_key" not in st.session_state:
    st.session_state.active_model_key = model_key
    st.session_state.params = {}

elif st.session_state.active_model_key != model_key:
    st.session_state.active_model_key = model_key
    st.session_state.params = {}

params = st.session_state.params
label_overrides = {}

# PARAMETER INPUTS
st.sidebar.subheader("Input Parameters")

# EXCEL-DRIVEN MODEL
if selected_model_file == "__EXCEL_DRIVEN__":

    uploaded_excel_model = st.sidebar.file_uploader(
        "Upload Excel model file (.xlsx)",
        type=["xlsx"],
        key="excel_model_uploader"
    )

    if uploaded_excel_model:

        # reset params if Excel file changes
        if (
                "excel_active_name" not in st.session_state
                or st.session_state.excel_active_name != uploaded_excel_model.name
        ):
            st.session_state.excel_active_name = uploaded_excel_model.name
            st.session_state.params = {}

        params = st.session_state.params

        # Load the defaults
        editable_defaults, _ = load_excel_params_defaults_with_computed(
            uploaded_excel_model,
            sheet_name=None,
            start_row=3
        )

        # Load Headers
        current_headers = get_scenario_headers(uploaded_excel_model)


        # RESET CALLBACK
        def handle_reset_excel():
            # 1. Reset Parameters
            reset_parameters_to_defaults(editable_defaults, params, uploaded_excel_model.name)
            # 2. Reset Header Labels
            if current_headers:
                for col_letter, default_text in current_headers.items():
                    st.session_state[f"label_override_{col_letter}"] = default_text


        # Display Button with Callback
        st.sidebar.button("Reset Parameters", on_click=handle_reset_excel)

        # Outcome Headers (Column B-E)
        if current_headers:
            with st.sidebar.expander("Output Scenario Headers", expanded=False):
                st.caption("Rename the output headers (B, C, D, E)")

                for col_letter in sorted(current_headers.keys()):
                    default_text = current_headers[col_letter]
                    widget_key = f"label_override_{col_letter}"

                    # Robust Widget Logic
                    if widget_key in st.session_state:
                        new_text = st.text_input(
                            f"Column {col_letter} Label",
                            key=widget_key
                        )
                    else:
                        new_text = st.text_input(
                            f"Column {col_letter} Label",
                            value=default_text,
                            key=widget_key
                        )
                    label_overrides[col_letter] = new_text

        # Render Main Parameters
        render_parameters_with_indent(
            editable_defaults,
            params,
            model_id=uploaded_excel_model.name
        )

    else:
        st.sidebar.info("Upload an Excel model file to edit parameters.")

# PYTHON MODEL
else:
    param_source = st.sidebar.radio(
        "Parameter Source",
        ["Model Default (YAML)", "Excel (.xlsx)", "YAML (.yaml)"],
        horizontal=True
    )

    uploaded_excel = None
    uploaded_yaml = None

    if param_source == "Excel (.xlsx)":
        uploaded_excel = st.sidebar.file_uploader("Upload Excel parameter file", type=["xlsx"])
    elif param_source == "YAML (.yaml)":
        uploaded_yaml = st.sidebar.file_uploader("Upload YAML parameter file", type=["yaml", "yml"])

    # PARAMETER SOURCE RESET LOGIC
    param_identity = (
        param_source,
        uploaded_excel.name if uploaded_excel else None,
        uploaded_yaml.name if uploaded_yaml else None,
    )

    if "active_param_identity" not in st.session_state:
        st.session_state.active_param_identity = param_identity
        st.session_state.params = {}
    elif st.session_state.active_param_identity != param_identity:
        st.session_state.active_param_identity = param_identity
        st.session_state.params = {}

    params = st.session_state.params

    if param_source == "YAML (.yaml)" and uploaded_yaml:
        raw = yaml.safe_load(uploaded_yaml) or {}
        model_defaults = flatten_dict(raw)
    else:
        model_defaults = load_model_params(
            selected_model_file,
            uploaded_excel=uploaded_excel
        )

    # Load Python Model Module to check for Labels
    model_module = load_model_from_file(selected_model_file)
    # Check for SCENARIO_LABELS constant in the python file
    current_headers = getattr(model_module, "SCENARIO_LABELS", None)

    if model_defaults:
        # Define Python Model Reset Callback
        def handle_reset_python():
            # 1. Reset Parameters
            reset_parameters_to_defaults(model_defaults, params, model_key)
            # 2. Reset Header Labels
            if current_headers:
                for key, default_text in current_headers.items():
                    # We use a unique key format for python models to avoid conflicts
                    st.session_state[f"py_label_{model_key}_{key}"] = default_text


        st.sidebar.button("Reset Parameters", on_click=handle_reset_python)

        # SCENARIO LABELS (PYTHON)
        if current_headers:
            with st.sidebar.expander("Output Scenario Headers", expanded=False):
                st.caption("Rename the output headers")

                for key, default_text in current_headers.items():
                    widget_key = f"py_label_{model_key}_{key}"

                    if widget_key in st.session_state:
                        new_val = st.text_input(f"Label for '{default_text}'", key=widget_key)
                    else:
                        new_val = st.text_input(f"Label for '{default_text}'", value=default_text, key=widget_key)

                    label_overrides[key] = new_val

        render_parameters_with_indent(
            model_defaults,
            params,
            model_id=model_key
        )
    else:
        st.sidebar.info("No default parameters defined for this model.")

# RUN SIMULATION
if st.sidebar.button("Run Simulation"):

    # EXCEL-DRIVEN MODEL RUN
    if selected_model_file == "__EXCEL_DRIVEN__":

        uploaded_excel_model = st.session_state.get("excel_model_uploader")

        if not uploaded_excel_model:
            st.error("Please upload an Excel model file first.")
            st.stop()

        with st.spinner(f"Running Excel-driven model: {uploaded_excel_model.name}..."):

            results = run_excel_driven_model(
                excel_file=uploaded_excel_model,
                filename=uploaded_excel_model.name,
                params=params,
                sheet_name=None,
                label_overrides=label_overrides
            )

            st.title(results.get("model_title", "Excel Driven Model"))
            st.write(results.get("model_description", ""))

            render_sections(results["sections"])

    # PYTHON MODEL RUN
    else:
        with st.spinner(f"Running {selected_label}..."):
            # Load module again (or reuse)
            model_module = load_model_from_file(selected_model_file)

            st.title(getattr(model_module, "model_title", app_config["title"]))
            st.write(getattr(model_module, "model_description", app_config["description"]))

            # Check if run_model accepts label_overrides
            sig = inspect.signature(model_module.run_model)
            if "label_overrides" in sig.parameters:
                results = model_module.run_model(params, label_overrides=label_overrides)
            else:
                results = model_module.run_model(params)

            sections = model_module.build_sections(results)
            render_sections(sections)
