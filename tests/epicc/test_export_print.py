from contextlib import nullcontext
from typing import Any

from epicc.ui import export
from epicc.ui.state import _PRINT_REQUESTED_KEY, _PRINT_TOKEN_KEY


def _fake_button(monkeypatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def button(label: str, **kwargs: Any) -> bool:
        captured["label"] = label
        captured.update(kwargs)
        # The click is delivered through the callback, never the return value.
        return False

    monkeypatch.setattr(export.st, "button", button)
    return captured


def test_pdf_button_requests_print_from_a_callback(monkeypatch) -> None:
    # A request read from the button's return value only reaches the page on the
    # rerun *after* the click, which made the button need two clicks.
    monkeypatch.setattr(export, "has_results", lambda: True)
    captured = _fake_button(monkeypatch)

    export.render_pdf_export_button()

    assert captured["on_click"] is export._request_print
    assert captured["disabled"] is False


def test_request_print_marks_a_fresh_request(monkeypatch) -> None:
    state: dict[str, Any] = {_PRINT_REQUESTED_KEY: False, _PRINT_TOKEN_KEY: 3}
    monkeypatch.setattr(export.st, "session_state", state)
    monkeypatch.setattr(export, "has_results", lambda: True)

    export._request_print()

    assert state[_PRINT_REQUESTED_KEY] is True
    # A new token so repeat clicks are not mistaken for the previous request.
    assert state[_PRINT_TOKEN_KEY] == 4


def test_request_print_ignored_without_results(monkeypatch) -> None:
    state: dict[str, Any] = {_PRINT_REQUESTED_KEY: False, _PRINT_TOKEN_KEY: 0}
    monkeypatch.setattr(export.st, "session_state", state)
    monkeypatch.setattr(export, "has_results", lambda: False)

    export._request_print()

    assert state[_PRINT_REQUESTED_KEY] is False
    assert state[_PRINT_TOKEN_KEY] == 0


def test_cancel_print_request_clears_a_pending_request(monkeypatch) -> None:
    state: dict[str, Any] = {_PRINT_REQUESTED_KEY: True, _PRINT_TOKEN_KEY: 1}
    monkeypatch.setattr(export.st, "session_state", state)

    export.cancel_print_request()

    assert state[_PRINT_REQUESTED_KEY] is False


class _Model:
    def human_name(self) -> str:
        return "Example Model"


def test_docx_button_is_ready_to_download_on_first_render(monkeypatch) -> None:
    """DOCX bytes must exist before the download button receives its click."""

    captured: dict[str, Any] = {}
    state: dict[str, Any] = {}
    output = {"value": 1}

    monkeypatch.setattr(export.st, "session_state", state)
    monkeypatch.setattr(export, "has_results", lambda: True)
    monkeypatch.setattr(export.st, "spinner", lambda _: nullcontext())
    monkeypatch.setattr(
        export,
        "_build_docx_export_bytes",
        lambda model, run_output: b"DOCX bytes",
    )
    monkeypatch.setattr(
        export.st,
        "download_button",
        lambda **kwargs: captured.update(kwargs),
    )

    export.render_docx_export_button(_Model(), output)

    assert captured["label"] == "Save report as DOCX"
    assert captured["data"] == b"DOCX bytes"
    assert "docx_data_example_model" in state


def test_docx_button_reuses_bytes_for_unchanged_results(monkeypatch) -> None:
    state: dict[str, Any] = {}
    output = {"value": 1}
    build_calls: list[None] = []

    monkeypatch.setattr(export.st, "session_state", state)
    monkeypatch.setattr(export, "has_results", lambda: True)
    monkeypatch.setattr(export.st, "spinner", lambda _: nullcontext())
    monkeypatch.setattr(
        export,
        "_build_docx_export_bytes",
        lambda model, run_output: build_calls.append(None) or b"DOCX bytes",
    )
    monkeypatch.setattr(export.st, "download_button", lambda **_: None)

    export.render_docx_export_button(_Model(), output)
    export.render_docx_export_button(_Model(), output)

    assert build_calls == [None]
