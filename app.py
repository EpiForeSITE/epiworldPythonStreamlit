import os
import yaml
import streamlit as st

from utils.model_loader import discover_models, load_model_from_file
from utils.parameter_loader import load_model_params
from utils.section_renderer import render_sections
from utils.parameter_ui import render_parameters_with_indent

# DIRECTORY & CONFIG
base_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base_dir, "config/app.yaml")) as f:
    app_config = yaml.safe_load(f)

with open(os.path.join(base_dir, "config/paths.yaml")) as f:
    path_config = yaml.safe_load(f)

# UI
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

model_options = {name: file for name, file in selected_models.items()}
model_options.update({f"Custom: {name}": file for name, file in custom_models.items()})

if not model_options:
    st.sidebar.warning("No valid model files found.")
    st.stop()

selected_label = st.sidebar.selectbox(
    "Select Model",
    list(model_options.keys())
)

selected_model_file = model_options[selected_label]

model_key = os.path.basename(selected_model_file)

# MODEL CHANGE
if "active_model_key" not in st.session_state:
    st.session_state.active_model_key = model_key
    st.session_state.params = {}

elif st.session_state.active_model_key != model_key:
    st.session_state.active_model_key = model_key
    st.session_state.params = {}

# PARAMETER INPUTS
st.sidebar.subheader("Input Parameters")

uploaded_excel = st.sidebar.file_uploader(
    "Upload Excel parameter file (optional)",
    type=["xlsx"]
)

params = st.session_state.params

model_defaults = load_model_params(
    selected_model_file,
    uploaded_excel=uploaded_excel
)

if model_defaults:
    render_parameters_with_indent(
        model_defaults,
        params,
        model_id=model_key
    )
else:
    st.sidebar.info("No default parameters defined for this model.")

# RUN SIMULATION
if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Running {selected_label}..."):
        model_module = load_model_from_file(selected_model_file)

        st.title(getattr(model_module, "model_title", app_config["title"]))
        st.write(getattr(model_module, "model_description", app_config["description"]))

        results = model_module.run_model(params)
        sections = model_module.build_sections(results)
        render_sections(sections)
