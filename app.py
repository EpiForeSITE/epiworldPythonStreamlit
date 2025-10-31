import os
import yaml
import streamlit as st
import streamlit.components.v1 as components

from utils.model_loader import load_model


#Load YAML
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "config.yaml")) as f:
    config = yaml.safe_load(f)

#App title & description
st.title(config["app"]["title"])
st.write(config["app"]["description"])

#Custom CSS for better sidebar clarity
#NEED ADJUSTMENT
st.markdown("""
    <style>
    /* Sidebar parameter section headings */
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

    /* Slight indentation for nested items */
    .sidebar-indent {
        margin-left: 15px;
    }
    </style>
""", unsafe_allow_html=True)


#Sidebar
st.sidebar.header("Simulation Controls")

#Model selection
model_map = {m["name"]: m["id"] for m in config["simulation_models"]}
selected_model_name = st.sidebar.selectbox("Select Model", list(model_map.keys()))
model_id = model_map[selected_model_name]

#Sidebar parameters
# st.sidebar.subheader("Model Parameters")
# params = {}
# for key, val in config["default_parameters"].items():
#     if isinstance(val, (float, int)):
#         params[key] = st.sidebar.number_input(key, value=val)
#     else:
#         params[key] = st.sidebar.text_input(key, value=str(val))

#Sidebar parameters with indentation and subtitles
st.sidebar.subheader("Input Parameters")
params = {}

def render_parameters(param_dict, level=0):
    """Recursively render parameters with styled subtitles and indentation."""
    for key, val in param_dict.items():
        if isinstance(val, dict):
            # Render section subtitle with custom CSS
            st.sidebar.markdown(
                f"<div class='sidebar-subtitle'>{key}</div>",
                unsafe_allow_html=True
            )
            render_parameters(val, level + 1)
        else:
            # Render input field with indentation
            container = st.sidebar.container()
            if level > 0:
                with container:
                    st.markdown("<div class='sidebar-indent'>", unsafe_allow_html=True)
                    if isinstance(val, (float, int)):
                        params[key] = st.number_input(key, value=val)
                    else:
                        params[key] = st.text_input(key, value=str(val))
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                if isinstance(val, (float, int)):
                    params[key] = st.sidebar.number_input(key, value=val)
                else:
                    params[key] = st.sidebar.text_input(key, value=str(val))

# Render nested YAML structure
render_parameters(config["default_parameters"])


#Run simulation
if st.sidebar.button("Run Simulation"):
    with st.spinner(f"Running {selected_model_name} model..."):
        run_model_func = load_model(model_id)
        html_table = run_model_func(params)
        st.subheader("Simulation Outcome")
        components.html(html_table, height=600, scrolling=True)

