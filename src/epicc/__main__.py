import hashlib
import importlib.resources
import re
from typing import Any

import streamlit as st
from pydantic import BaseModel, ValidationError

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
    item_level,
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

    upload_bytes = uploaded_excel_model.getvalue()
    upload_hash = hashlib.sha1(upload_bytes).hexdigest()
    excel_identity = (uploaded_excel_model.name, len(upload_bytes), upload_hash)
    should_refresh_params = False
    if st.session_state.get("excel_active_identity") != excel_identity:
        st.session_state.excel_active_identity = excel_identity
        st.session_state.params = {}
        params = st.session_state.params
        should_refresh_params = True

    uploaded_excel_name = uploaded_excel_model.name

    editable_defaults, _ = load_excel_params_defaults_with_computed(
        uploaded_excel_model, sheet_name=None, start_row=3
    )
    current_headers = get_scenario_headers(uploaded_excel_model)

    def handle_reset_excel() -> None:
        reset_parameters_to_defaults(editable_defaults, params, uploaded_excel_name)
        for col_letter, default_text in current_headers.items():
            st.session_state[f"label_override_{col_letter}"] = default_text

    if should_refresh_params:
        handle_reset_excel()

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
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any], bool]:
    label_overrides: dict[str, str] = {}

    sorted_suffixes = sorted(VALID_PARAMETER_SUFFIXES)
    uploaded_params = st.sidebar.file_uploader(
        "Optional parameter override file",
        type=sorted_suffixes,
        help="If omitted, model defaults are used.",
    )

    if uploaded_params:
        upload_bytes = uploaded_params.getvalue()
        upload_hash = hashlib.sha1(upload_bytes).hexdigest()
        param_identity = (
            "upload",
            uploaded_params.name,
            len(upload_bytes),
            upload_hash,
        )
    else:
        param_identity = ("default", None, 0, None)
    should_refresh_params = False
    if st.session_state.get("active_param_identity") != param_identity:
        st.session_state.active_param_identity = param_identity
        st.session_state.params = {}
        params = st.session_state.params
        should_refresh_params = True

    try:
        model_defaults = load_model_params(
            model,
            uploaded_params=uploaded_params or None,
            uploaded_name=uploaded_params.name if uploaded_params else None,
        )
    except ValidationError as exc:
        _render_validation_error_details(model.human_name(), exc, sidebar=True)
        return params, label_overrides, {}, True
    except ValueError as exc:
        st.sidebar.error(
            f"Could not read parameter file for {model.human_name()}: {exc}"
        )
        return params, label_overrides, {}, True

    if not model_defaults:
        st.sidebar.info("No default parameters defined for this model.")
        return params, label_overrides, {}, True

    current_headers = model.scenario_labels

    def handle_reset_python() -> None:
        reset_parameters_to_defaults(model_defaults, params, model_key)
        if not current_headers:
            return

        for key, default_text in current_headers.items():
            st.session_state[f"py_label_{model_key}_{key}"] = default_text

    if should_refresh_params:
        handle_reset_python()

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
    return params, label_overrides, model_defaults, False


def _unflatten_indented_params(flat_params: dict[str, Any]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[dict[str, Any]] = [root]

    for raw_key, value in flat_params.items():
        level = item_level(raw_key)
        label = raw_key.strip()

        while len(stack) > level + 1:
            stack.pop()

        parent = stack[-1]
        if value is None:
            node: dict[str, Any] = {}
            parent[label] = node
            stack.append(node)
            continue

        parent[label] = value

    return root


def _merge_sidebar_values(
    nested_defaults: dict[str, Any], params: dict[str, Any]
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in nested_defaults.items():
        if isinstance(value, dict):
            merged[key] = _merge_sidebar_values(value, params)
            continue

        merged[key] = params.get(key, value)

    return merged


def _build_typed_params(
    model: BaseSimulationModel,
    model_defaults_flat: dict[str, Any],
    params: dict[str, Any],
) -> BaseModel:
    nested_defaults = _unflatten_indented_params(model_defaults_flat)
    payload = _merge_sidebar_values(nested_defaults, params)
    return model.parameter_model().model_validate(payload)


def _render_validation_error_details(
    model_name: str, exc: ValidationError, sidebar: bool
) -> None:
    target = st.sidebar if sidebar else st
    issues = exc.errors()
    issue_count = len(issues)
    target.error(f"Parameters do not match {model_name} schema ({issue_count} issues).")

    details = target.expander("Validation details", expanded=False)
    with details:
        preview_count = 8
        for issue in issues[:preview_count]:
            loc_parts = issue.get("loc", [])
            path = " > ".join(str(p) for p in loc_parts) if loc_parts else "(root)"
            msg = issue.get("msg", "Invalid value")
            st.write(f"- {path}: {msg}")

        if issue_count > preview_count:
            st.caption(f"...and {issue_count - preview_count} more.")

        safe_model_name = re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")
        full_details = exc.json(indent=2)
        detail_digest = hashlib.sha1(full_details.encode("utf-8")).hexdigest()[:10]
        st.text_area(
            "Full details (copyable)",
            value=full_details,
            height=180,
            key=f"{safe_model_name}_{'sidebar' if sidebar else 'main'}_validation_text_{detail_digest}",
        )
        st.download_button(
            "Download full error details",
            data=full_details,
            file_name=f"{safe_model_name}_validation_error.json",
            mime="application/json",
            key=f"{safe_model_name}_{'sidebar' if sidebar else 'main'}_validation_download_{detail_digest}",
        )


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
    typed_params: BaseModel,
    label_overrides: dict[str, str],
) -> None:
    with st.spinner(f"Running {selected_label}..."):
        st.title(model.model_title or CONFIG.app.title)
        st.write(model.model_description or CONFIG.app.description)
        results = model.run(typed_params, label_overrides=label_overrides)
        render_sections(model.build_sections(results))


_load_styles()

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

has_input_errors = False
typed_params: BaseModel | None = None

if is_excel_model:
    params, label_overrides = _render_excel_parameter_inputs(params)
    model_defaults_flat: dict[str, Any] = {}
else:
    params, label_overrides, model_defaults_flat, has_input_errors = (
        _render_python_parameter_inputs(
            model_registry[selected_label],
            model_key,
            params,
        )
    )

    if not has_input_errors:
        try:
            typed_params = _build_typed_params(
                model_registry[selected_label], model_defaults_flat, params
            )
        except ValidationError as exc:
            _render_validation_error_details(selected_label, exc, sidebar=True)
            has_input_errors = True

if not st.sidebar.button("Run Simulation", disabled=has_input_errors):
    st.stop()

if is_excel_model:
    _run_excel_simulation(params, label_overrides)
    st.stop()

if typed_params is None:
    st.error("Cannot run simulation until parameter validation errors are fixed.")
    st.stop()

_run_python_simulation(
    selected_label,
    model_registry[selected_label],
    typed_params,
    label_overrides,
)
