import streamlit as st

def render_sections(sections):
    for i, section in enumerate(sections):

        # Section title
        st.markdown(f"## {section['title']}")

        # Render all content blocks inside the section
        for block in section["content"]:
            if hasattr(block, "columns"):  # DataFrame check
                st.table(block)
            elif isinstance(block, str):  # Markdown string
                st.markdown(block, unsafe_allow_html=True)
            else:
                st.write(block)  # fallback

        # Divider between sections
        if i < len(sections) - 1:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
