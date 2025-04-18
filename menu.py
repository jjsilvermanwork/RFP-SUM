import streamlit as st
from PIL import Image
import uuid

def menu(is_uploaded=False, is_summarized=False):
    # Custom CSS for sidebar and page background
    new_style = """
        <style>
        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        div[data-testid="stDecoration"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        div[data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        MainMenu {
            visibility: hidden;
            height: 0%;
        }
        header {
            visibility: hidden;
            height: 0%;
        }
        footer {
            visibility: hidden;
            height: 0%;
        }
        img[data-testid="stLogo"] {
            height: 4rem;
            position: centered
        }
        </style>
        """

    # Applies the CSS Injection
    st.markdown(new_style, unsafe_allow_html=True)

    # Generates a flag to determine if the gen_summary variable is initialized
    if "gen_summary" not in st.session_state:
        st.session_state.gen_summary = False

    # Load the logo image
    image = Image.open('images/logo3.png')
    # Use logo for Side Panel
    st.sidebar.image(image, use_column_width=True)

    # Generate a unique identifier for this instance of the menu
    unique_id = str(uuid.uuid4())

    # Determine what pages are available on the side panel based on the logic of what is uploaded
    st.sidebar.markdown("### Navigation")
    st.sidebar.button("Home", on_click=lambda: st.experimental_set_query_params(page="Home"), key=f"home_button_{unique_id}")

    st.sidebar.markdown("### RFP Summarizer")
    st.sidebar.button("RFP Home", on_click=lambda: st.experimental_set_query_params(page="RFP_Home"), key=f"rfp_home_button_{unique_id}")

    if is_uploaded and not is_summarized:  # Before Requirements uploaded
        st.sidebar.button("RFI/RFP Requirements", on_click=lambda: st.experimental_set_query_params(page="RFP_Requirements"), key=f"rfp_requirements_button_{unique_id}")
        st.sidebar.button("RFI/RFP Chat", on_click=lambda: st.experimental_set_query_params(page="Chat"), key=f"rfp_chat_button_{unique_id}")

    if is_uploaded and is_summarized:  # After requirements uploaded
        st.sidebar.button("RFI/RFP Requirements", on_click=lambda: st.experimental_set_query_params(page="RFP_Requirements"), key=f"rfp_requirements_button_{unique_id}")
        st.sidebar.button("RFI/RFP Summary", on_click=lambda: st.experimental_set_query_params(page="Summary"), key=f"rfp_summary_button_{unique_id}")
        st.sidebar.button("RFI/RFP Chat", on_click=lambda: st.experimental_set_query_params(page="Chat"), key=f"rfp_chat_button_{unique_id}")

    # Adding Resume Retooler navigation
    st.sidebar.markdown("### Resume Retooler")
    st.sidebar.button("Resume Retooler Home", on_click=lambda: st.experimental_set_query_params(page="Resume_Retooler_Home"), key=f"resume_retooler_home_button_{unique_id}")

if __name__ == "__main__":
    menu()









