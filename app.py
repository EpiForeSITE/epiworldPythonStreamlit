import os
import yaml
import streamlit as st

from utils.model_loader import discover_models, load_model_from_file
from utils.parameter_loader import load_model
from utils.section_renderer import render_sections

base_dir = os.path.dirname(os.path.abspath(__file__))

# Load app metadata
with open(os.path.join(base_dir, "config/app.yaml")) as f:
    app_config = yaml.safe_load(f)

# Load model paths
with open(os.path.join(base_dir, "config/paths.yaml")) as f:
    path_config = yaml.safe_load(f)

# Load global defaults
with open(os.path.join(base_dir, "config/global_defaults.yaml")) as f:
    global_defaults = yaml.safe_load(f)

# Placeholder — actual values will be loaded after model selection
selected_title = app_config["title"]
selected_description = app_config["description"]

#  CSS LOADING
def load_css(file_path: str):
    with open(file_path) as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("styles/sidebar.css")

#  MODEL SELECTION
st.sidebar.header("Simulation Controls")

selected_path = os.path.join(base_dir, path_config["model_paths"]["selected_path"])
default_custom_path = os.path.join(base_dir, path_config["model_paths"]["custom_path"])

# Override custom path
user_custom_path = st.sidebar.text_input("Custom Models Folder", value=default_custom_path)

selected_models = discover_models(selected_path)
custom_models = discover_models(user_custom_path)

# Combine model options
model_options = {f"{name}": file for name, file in selected_models.items()}
model_options.update({f"Custom: {name}": file for name, file in custom_models.items()})

if not model_options:
    st.sidebar.warning("No valid model files found.")
    st.stop()

selected_label = st.sidebar.selectbox("Select Model", list(model_options.keys()))
selected_model_file = model_options[selected_label]


# PARAMETER INPUTS
st.sidebar.subheader("Input Parameters")

params = {}

def render_parameters(param_dict):
    """
    Renders YAML-based parameters into Streamlit inputs.
    - dict values → collapsible sections
    - other values → normal input fields
    """
    for key, val in param_dict.items():

        # Collapsible section
        if isinstance(val, dict):
            with st.sidebar.expander(key, expanded=False):
                for subkey, subval in val.items():
                    params[subkey] = st.text_input(subkey, value=str(subval))

            # Single value
        else:
            params[key] = st.sidebar.text_input(key, value=str(val))

# Load default parameters for selected model
model_defaults = load_model(selected_model_file)

if model_defaults:
    render_parameters(model_defaults)
else:
    st.sidebar.info("No default parameters defined for this model.")

#  RUN SIMULATION
if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Running model: {selected_label}..."):

        # Load the model module
        model_module = load_model_from_file(selected_model_file)

        # Override title & description if the model provides its own metadata
        selected_title = getattr(model_module, "model_title", app_config["title"])
        selected_description = getattr(model_module, "model_description", app_config["description"])

        st.title(selected_title)
        st.write(selected_description)

        # Run the model
        results = model_module.run_model(params)

        # Build UI layout for the model
        sections = model_module.build_sections(results)

        # Render all sections
        render_sections(sections)

