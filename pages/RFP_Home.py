import streamlit as st
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Please replace st.experimental_set_query_params with st.query_params")
warnings.filterwarnings("ignore", category=UserWarning, message="The use_column_width parameter has been deprecated")
warnings.filterwarnings("ignore", category=UserWarning, message="Please replace st.experimental_get_query_params with st.query_params")

import time
from backend.ingestion_utils import upload_pdf_extract_reqs  # Uncomment if needed
from PIL import Image

def run():
    # Custom CSS for sidebar and page background
    new_style = """
        <style>
        div[data-testid="stAppViewContainer"] {
            background-color: #FFFFFF;
            color: #070F26;
        }
        div[data-testid="stSideBar"] {
            background-color: #070F26;
        }
        div[data-testid="stToolbar"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"],
        MainMenu, header, footer, img[data-testid="stLogo"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        .st-pagelink {
            color: #FFFFFF;
        }
        </style>
        """

    # Applies the CSS Injection
    st.markdown(new_style, unsafe_allow_html=True)

    # Title
    title_alignment = """
    <h1 style="font-size: 42px; text-align: center;">NTT DATA RFP Summarization Tool</h1>
    """
    st.markdown(title_alignment, unsafe_allow_html=True)

    # Initialize session state variables
    if 'rfp_selection' not in st.session_state:
        st.session_state.rfp_selection = None
    if 'uploaded_response_files' not in st.session_state:
        st.session_state.uploaded_response_files = None

    # File uploader form
    with st.form('file_selection'):
        st.markdown('Upload *pdf files* for the proposal and proposal responses below:')
        rfp_selection = st.file_uploader('Upload the original RFI/RFP file', type=['pdf'])
        uploaded_response_files = st.file_uploader("Upload the RFI/RFP responses", type=['pdf'], accept_multiple_files=True)
        st.session_state.rfp_selection = rfp_selection
        st.session_state.uploaded_response_files = uploaded_response_files

        with st.columns([4, 1])[1]:
            submitted = st.form_submit_button("Generate Requirements")

            if submitted:
                if rfp_selection and uploaded_response_files:
                    # Call your function to process the files
                    # upload_pdf_extract_reqs(st)
                    st.write("Processing...")
                    time.sleep(2)  # Simulate processing time
                    st.success("Requirements generated!")
                    # Switch to the requirements page
                    st.experimental_set_query_params(page="RFP_Requirements")
                else:
                    st.warning("Please upload both the RFP file and the response files.")

if __name__ == "__main__":
    run()
