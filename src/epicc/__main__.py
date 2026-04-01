import importlib.resources
from typing import Any

import streamlit as st

from epicc.config import CONFIG
from epicc.formats import VALID_PARAMETER_SUFFIXES
from epicc.model.base import BaseSimulationModel
from epicc.utils.excel_model_runner import (
    get_scenario_headers,
    load_excel_params_defaults_with_computed,
    run_excel_driven_model,
)
from epicc.utils.model_loader import get_built_in_models
from epicc.utils.parameter_loader import load_model_params
from epicc.utils.parameter_ui import (
    render_parameters_with_indent,
    reset_parameters_to_defaults,
)
from epicc.utils.section_renderer import render_sections


def _load_styles() -> None:
    with importlib.resources.files("epicc").joinpath("web/sidebar.css").open("rb") as f:
        css_content = f.read().decode("utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def _sync_active_model(model_key: str) -> dict[str, Any]:
    active_model_key = st.session_state.get("active_model_key")
    if active_model_key != model_key:
        st.session_state.active_model_key = model_key
        st.session_state.params = {}

    if "params" not in st.session_state:
        st.session_state.params = {}

    return st.session_state.params


def _render_excel_parameter_inputs(
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    label_overrides: dict[str, str] = {}

    uploaded_excel_model = st.sidebar.file_uploader(
        "Upload Excel model file (.xlsx)", type=["xlsx"], key="excel_model_uploader"
    )
    if not uploaded_excel_model:
        st.sidebar.info("Upload an Excel model file to edit parameters.")
        return params, label_overrides

    uploaded_excel_name = uploaded_excel_model.name
    if st.session_state.get("excel_active_name") != uploaded_excel_name:
        st.session_state.excel_active_name = uploaded_excel_name
        st.session_state.params = {}
        params = st.session_state.params

    editable_defaults, _ = load_excel_params_defaults_with_computed(
        uploaded_excel_model, sheet_name=None, start_row=3
    )
    current_headers = get_scenario_headers(uploaded_excel_model)

    def handle_reset_excel() -> None:
        reset_parameters_to_defaults(editable_defaults, params, uploaded_excel_name)
        for col_letter, default_text in current_headers.items():
            st.session_state[f"label_override_{col_letter}"] = default_text

    st.sidebar.button("Reset Parameters", on_click=handle_reset_excel)

    if current_headers:
        with st.sidebar.expander("Output Scenario Headers", expanded=False):
            st.caption("Rename the output headers (B, C, D, E)")
            for col_letter in sorted(current_headers.keys()):
                default_text = current_headers[col_letter]
                widget_key = f"label_override_{col_letter}"
                if widget_key in st.session_state:
                    label_overrides[col_letter] = st.text_input(
                        f"Column {col_letter} Label", key=widget_key
                    )
                    continue

                label_overrides[col_letter] = st.text_input(
                    f"Column {col_letter} Label",
                    value=default_text,
                    key=widget_key,
                )

    render_parameters_with_indent(
        editable_defaults, params, model_id=uploaded_excel_name
    )
    return params, label_overrides


def _render_python_parameter_inputs(
    model: BaseSimulationModel,
    model_key: str,
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    label_overrides: dict[str, str] = {}

    sorted_suffixes = sorted(VALID_PARAMETER_SUFFIXES)
    uploaded_params = st.sidebar.file_uploader(
        "Optional parameter override file",
        type=sorted_suffixes,
        help="If omitted, model defaults are used.",
    )

    param_identity = (
        "upload" if uploaded_params else "default",
        uploaded_params.name if uploaded_params else None,
    )
    if st.session_state.get("active_param_identity") != param_identity:
        st.session_state.active_param_identity = param_identity
        st.session_state.params = {}
        params = st.session_state.params

    model_defaults = load_model_params(
        model,
        uploaded_params=uploaded_params or None,
        uploaded_name=uploaded_params.name if uploaded_params else None,
    )

    if not model_defaults:
        st.sidebar.info("No default parameters defined for this model.")
        return params, label_overrides

    current_headers = model.scenario_labels

    def handle_reset_python() -> None:
        reset_parameters_to_defaults(model_defaults, params, model_key)
        if not current_headers:
            return

        for key, default_text in current_headers.items():
            st.session_state[f"py_label_{model_key}_{key}"] = default_text

    st.sidebar.button("Reset Parameters", on_click=handle_reset_python)

    if current_headers:
        with st.sidebar.expander("Output Scenario Headers", expanded=False):
            st.caption("Rename the output headers")
            for key, default_text in current_headers.items():
                widget_key = f"py_label_{model_key}_{key}"
                default_label = str(default_text)
                if widget_key in st.session_state:
                    label_overrides[key] = st.text_input(
                        f"Label for '{default_label}'", key=widget_key
                    )
                    continue

                label_overrides[key] = st.text_input(
                    f"Label for '{default_label}'",
                    value=default_label,
                    key=widget_key,
                )

    render_parameters_with_indent(model_defaults, params, model_id=model_key)
    return params, label_overrides


def _run_excel_simulation(
    params: dict[str, Any], label_overrides: dict[str, str]
) -> None:
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
            label_overrides=label_overrides,
        )
        st.title(results.get("model_title", "Excel Driven Model"))
        st.write(results.get("model_description", ""))
        render_sections(results["sections"])


def _run_python_simulation(
    selected_label: str,
    model: BaseSimulationModel,
    params: dict[str, Any],
    label_overrides: dict[str, str],
) -> None:
    with st.spinner(f"Running {selected_label}..."):
        st.title(model.model_title or CONFIG.app.title)
        st.write(model.model_description or CONFIG.app.description)
        results = model.run(params, label_overrides=label_overrides)
        render_sections(model.build_sections(results))


st.set_page_config(
    page_title="EpiCON Cost Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

_load_styles()

st.sidebar.title("EpiCON Cost Calculator")
st.sidebar.header("Simulation Controls")

built_in_models = get_built_in_models()
model_registry: dict[str, BaseSimulationModel] = {
    m.human_name(): m for m in built_in_models
}
model_labels = [*model_registry.keys(), "Excel Driven Model"]

selected_label = st.sidebar.selectbox("Select Model", model_labels, index=0)
is_excel_model = selected_label == "Excel Driven Model"
model_key = selected_label

params = _sync_active_model(model_key)

st.sidebar.subheader("Input Parameters")

if is_excel_model:
    params, label_overrides = _render_excel_parameter_inputs(params)
else:
    params, label_overrides = _render_python_parameter_inputs(
        model_registry[selected_label],
        model_key,
        params,
    )

if not st.sidebar.button("Run Simulation"):
    st.stop()

if is_excel_model:
    _run_excel_simulation(params, label_overrides)
    st.stop()

_run_python_simulation(
    selected_label, model_registry[selected_label], params, label_overrides
)
