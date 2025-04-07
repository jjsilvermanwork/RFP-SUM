import streamlit as st 
import time
from backend.ingestion_utils import upload_pdf_extract_reqs # this needs to be commented out
from PIL import Image
from pages.menu import menu # what is visible on the side bar prior to document submission

import requests 
import certifi

response = requests.get("https://rfpsummmaryaisearch.search.windows.net", verify=False)


# Custom CSS for sidebar and page background
new_style = """
        <style>
        # div[data-testid="stAppViewContainer"] {
        # background-color: #FFFFFF;
        # color: #070F26
        # }
        #div[data-testid="stSideBar"]{
        #background-color: #070F26;
        #}
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
        .st-pagelink {
            color: #FFFFFF;
        }
        </style>
        """

# Applies the CSS Injection
st.markdown(new_style, unsafe_allow_html=True)

# Loads a logo from file and applies it
image = Image.open('images/logo3.png')
st.logo(image, size="large", link=None, icon_image=None)

# Calls menu with values passed to determine what
menu(False, False)

# Title
title_alignment = """
<h1 style="font-size: 42px; text-align: center;">NTT DATA RFP Summarization Tool</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

if 'rfp_selection' not in st.session_state:
    st.session_state.rfp_selection = ''
if 'uploaded_response_files' not in st.session_state:
    st.session_state.uploaded_response_files = ''

with st.form('file_selection'):
    st.markdown('Upload *pdf files* for the proposal and proposal responses below:')
    rfp_selection = st.file_uploader('Upload the original RFI/RFP file', type=['pdf'])
    uploaded_response_files = st.file_uploader("Upload the RFI/RFP responses", type=['pdf'], accept_multiple_files=True)
    st.session_state.rfp_selection = rfp_selection
    st.session_state.uploaded_response_files = uploaded_response_files

    with st.columns([4, 1])[1]:
        submitted = st.form_submit_button("Generate Requirements", use_container_width = True)

        if submitted:
            upload_pdf_extract_reqs(st)
            st.switch_page("pages/1_RFP_Requirements.py")



