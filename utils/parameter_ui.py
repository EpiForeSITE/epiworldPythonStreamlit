import streamlit as st


def reset_parameters_to_defaults(
    param_dict: dict, params: dict, model_id: str
) -> None:
    """Reset editable parameters to their default values."""
    for label, value in param_dict.items():
        clean_label = str(label).lstrip("\t")

        if value is None:
            continue

        params[clean_label] = value
        st.session_state[f"{model_id}_{clean_label}"] = str(value)


def render_parameters_with_indent(
    param_dict: dict, params: dict, model_id: str
) -> None:
    """Render parameter inputs without overwriting defaults with blank values."""
    for label, value in param_dict.items():
        indent_level = len(label) - len(label.lstrip("\t"))
        clean_label = label.lstrip("\t")

        if value is None:
            st.sidebar.markdown(
                (
                    f"<div style='margin-left:{indent_level * 1.5}em; "
                    f"font-weight:600;'>{clean_label}</div>"
                ),
                unsafe_allow_html=True,
            )
            continue

        widget_key = f"{model_id}_{clean_label}"
        current_value = params.get(clean_label, value)

        user_value = st.sidebar.text_input(
            clean_label,
            value=str(current_value),
            key=widget_key,
        )

        if str(user_value).strip():
            params[clean_label] = user_value
        else:
            params.setdefault(clean_label, value)
