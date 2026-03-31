from typing import Any

import streamlit as st
from streamlit.components.v1 import html

RESULTS_PAYLOAD_KEY = "results_payload"
PRINT_REQUESTED_KEY = "print_requested"
PRINT_TRIGGER_TOKEN_KEY = "print_trigger_token"


def initialize_export_state() -> None:
    if RESULTS_PAYLOAD_KEY not in st.session_state:
        st.session_state[RESULTS_PAYLOAD_KEY] = None

    if PRINT_REQUESTED_KEY not in st.session_state:
        st.session_state[PRINT_REQUESTED_KEY] = False

    if PRINT_TRIGGER_TOKEN_KEY not in st.session_state:
        st.session_state[PRINT_TRIGGER_TOKEN_KEY] = 0


def clear_export_state() -> None:
    st.session_state[RESULTS_PAYLOAD_KEY] = None
    st.session_state[PRINT_REQUESTED_KEY] = False
    st.session_state[PRINT_TRIGGER_TOKEN_KEY] = 0


def has_results() -> bool:
    return st.session_state.get(RESULTS_PAYLOAD_KEY) is not None


def get_results_payload() -> dict[str, Any] | None:
    payload = st.session_state.get(RESULTS_PAYLOAD_KEY)
    if payload is None:
        return None

    return payload


def set_results_payload(payload: dict[str, Any] | None) -> None:
    st.session_state[RESULTS_PAYLOAD_KEY] = payload


def render_export_button() -> None:
    export_clicked = st.sidebar.button(
        "Export Results as PDF", disabled=not has_results()
    )
    if export_clicked and has_results():
        st.session_state[PRINT_REQUESTED_KEY] = True
        st.session_state[PRINT_TRIGGER_TOKEN_KEY] = (
            st.session_state.get(PRINT_TRIGGER_TOKEN_KEY, 0) + 1
        )


def trigger_print_if_requested() -> None:
    if not st.session_state.get(PRINT_REQUESTED_KEY):
        return

    if not has_results():
        st.session_state[PRINT_REQUESTED_KEY] = False
        return

    trigger_token = st.session_state.get(PRINT_TRIGGER_TOKEN_KEY, 0)
    html(
        (
            "<script>"
            f"window.__epiccPrintToken = {trigger_token};"
            "setTimeout(function(){ window.parent.print(); }, 0);"
            "</script>"
        ),
        height=0,
    )
    st.session_state[PRINT_REQUESTED_KEY] = False
