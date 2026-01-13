import streamlit as st


def render_parameters_with_indent(param_dict, params, model_id):
    """
    Render hierarchical parameters with indentation-based expanders.

    param_dict: flattened dict with tab-indented keys
    params: session_state params dict
    model_id: unique identifier for current model (used for widget keys)
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

                # If we hit a sibling or parent level, stop
                if sublevel <= level:
                    break

                # Only collect direct children
                if sublevel == level + 1 and subval is not None:
                    sublabel = subkey.strip()
                    children.append((sublabel, subval))

                j += 1

            # Render the expander with all children inside
            with st.sidebar.expander(label, expanded=False):
                for sublabel, subval in children:
                    widget_key = f"{model_id}:{label}:{sublabel}"
                    # Use st.text_input (without sidebar) since we're inside sidebar.expander
                    params[sublabel] = st.text_input(
                        sublabel,
                        value=str(subval),
                        key=widget_key
                    )

            # Move i to where we stopped collecting
            i = j
            continue

        # TOP-LEVEL PARAMS
        widget_key = f"{model_id}:{label}"

        params[label] = st.sidebar.text_input(
            label,
            value=str(value),
            key=widget_key
        )
        i += 1