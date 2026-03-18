import streamlit as st


def reset_parameters_to_defaults(param_dict, params, model_id):
    """
    Resets Streamlit session state widgets and params dict to values found in param_dict.
    """
    items = list(param_dict.items())
    i = 0
    n = len(items)

    while i < n:
        key, value = items[i]
        level = len(key) - len(key.lstrip("\t"))
        label = key.strip()

        if value is None:
            # Handle Children
            j = i + 1
            while j < n:
                subkey, subval = items[j]
                sublevel = len(subkey) - len(subkey.lstrip("\t"))

                if sublevel <= level:
                    break

                # Reset logic for child
                if sublevel == level + 1 and subval is not None:
                    sublabel = subkey.strip()
                    widget_key = f"{model_id}:{label}:{sublabel}"

                    st.session_state[widget_key] = str(subval)
                    params[sublabel] = str(subval)
                j += 1
            i = j
            continue

        # Reset logic for Top-level
        widget_key = f"{model_id}:{label}"
        st.session_state[widget_key] = str(value)
        params[label] = str(value)
        i += 1


def render_parameters_with_indent(param_dict, params, model_id):
    """
    Render hierarchical parameters with indentation-based expanders.
    Checks session_state before setting 'value' to avoid DuplicateWidgetID/API warnings.
    """
    items = list(param_dict.items())
    i = 0
    n = len(items)

    while i < n:
        key, value = items[i]

        level = len(key) - len(key.lstrip("\t"))
        label = key.strip()

        if value is None:
            # Collect all children
            children = []
            j = i + 1
            while j < n:
                subkey, subval = items[j]
                sublevel = len(subkey) - len(subkey.lstrip("\t"))

                if sublevel <= level:
                    break

                if sublevel == level + 1 and subval is not None:
                    sublabel = subkey.strip()
                    children.append((sublabel, subval))

                j += 1

            # Render the expander with all children inside
            with st.sidebar.expander(label, expanded=False):
                for sublabel, subval in children:
                    widget_key = f"{model_id}:{label}:{sublabel}"
                    if widget_key in st.session_state:
                        params[sublabel] = st.text_input(
                            sublabel,
                            key=widget_key
                        )
                    else:
                        # First load: Pass the default value
                        params[sublabel] = st.text_input(
                            sublabel,
                            value=str(subval),
                            key=widget_key
                        )

            i = j
            continue

        # TOP-LEVEL PARAMS
        widget_key = f"{model_id}:{label}"

        if widget_key in st.session_state:
            params[label] = st.sidebar.text_input(
                label,
                key=widget_key
            )
        else:
            params[label] = st.sidebar.text_input(
                label,
                value=str(value),
                key=widget_key
            )
        i += 1
