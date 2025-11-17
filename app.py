import os
import yaml
import streamlit as st
import streamlit.components.v1 as components

from utils.model_loader import discover_models, load_model_from_file
from utils.parameter_loader import load_model_defaults   # <-- NEW

# Load yaml
base_dir = os.path.dirname(os.path.abspath(__file__))

# Load app title/description
with open(os.path.join(base_dir, "config/app.yaml")) as f:
    app_config = yaml.safe_load(f)

# Load model paths
with open(os.path.join(base_dir, "config/paths.yaml")) as f:
    path_config = yaml.safe_load(f)

# Load global defaults
with open(os.path.join(base_dir, "config/global_defaults.yaml")) as f:
    global_defaults = yaml.safe_load(f)


# App title & description
st.title(app_config["title"])
st.write(app_config["description"])


# CSS (sidebar headings)
st.markdown("""
    <style>
    .sidebar-subtitle {
        background-color: #2a2a2a;
        color: #ffffff;
        padding: 6px 10px;
        margin-top: 10px;
        margin-bottom: 5px;
        border-left: 4px solid #00c0ff;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .sidebar-indent {
        margin-left: 15px;
    }
    </style>
""", unsafe_allow_html=True)


# Sidebar main header
st.sidebar.header("Simulation Controls")

# MODEL SELECTION

default_path = os.path.join(base_dir, path_config["model_paths"]["default_path"])
custom_path = os.path.join(base_dir, path_config["model_paths"]["custom_path"])

user_custom_path = st.sidebar.text_input("Custom Models Folder", value=custom_path)

default_models = discover_models(default_path)
custom_models = discover_models(user_custom_path)

model_options = {f"Default: {name}": file for name, file in default_models.items()}
model_options.update({f"Custom: {name}": file for name, file in custom_models.items()})

if not model_options:
    st.sidebar.warning("No model files found in models/ or custom_models/")
    st.stop()

selected_label = st.sidebar.selectbox("Select Model", list(model_options.keys()))
selected_model_file = model_options[selected_label]

# SIDEBAR — PARAMETERS (Collapsible Sections)
st.sidebar.subheader("Input Parameters")

params = {}

def render_parameters(param_dict):
    """
    Rules:
    - If a key's value is a dict → render as collapsible section
    - If not → render as a normal parameter (not collapsible)
    """
    for key, val in param_dict.items():

        # Collapsible section (only for dicts)
        if isinstance(val, dict):
            with st.sidebar.expander(key, expanded=False):
                for subkey, subval in val.items():
                    if isinstance(subval, (float, int)):
                        params[subkey] = st.number_input(subkey, value=subval)
                    else:
                        params[subkey] = st.text_input(subkey, value=str(subval))

        # Normal parameter (not collapsible)
        else:
            if isinstance(val, (float, int)):
                params[key] = st.sidebar.number_input(key, value=val)
            else:
                params[key] = st.sidebar.text_input(key, value=str(val))


# Load default parameters for selected model
model_defaults = load_model_defaults(selected_model_file)

if model_defaults:
    render_parameters(model_defaults)
else:
    st.sidebar.info("No default parameters for this model.")

# RUN SIMULATION BUTTON

if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Running model: {selected_label}..."):
        run_model_func = load_model_from_file(selected_model_file)
        html_output = run_model_func(params)

        st.subheader("Simulation Outcome")
        components.html(html_output, height=600, scrolling=True)
