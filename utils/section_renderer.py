import streamlit as st
import html


def render_sections(sections: list[dict]) -> None:
    """
    Render output sections from model results.

    Escapes user-supplied content to prevent HTML injection attacks.

    Args:
        sections: List of section dicts with 'title' and 'content' keys
    """
    for i, section in enumerate(sections):
        # Section title - escape user-supplied text
        section_title = html.escape(str(section.get("title", "")))
        st.markdown(f"## {section_title}")

        # Render all content blocks inside the section
        for block in section.get("content", []):
            if hasattr(block, "columns"):  # DataFrame check
                st.table(block)
            elif isinstance(block, str):  # Markdown string
                # Escape user-supplied markdown to prevent injection
                safe_block = html.escape(block)
                st.markdown(safe_block, unsafe_allow_html=False)
            else:
                st.write(block)  # fallback

        # Divider between sections (hardcoded, no user input)
        if i < len(sections) - 1:
            st.markdown(
                '<div class="section-divider"></div>',
                unsafe_allow_html=True
            )
