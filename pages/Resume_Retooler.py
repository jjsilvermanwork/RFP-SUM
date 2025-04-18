import os
import io
import streamlit as st
from PIL import Image
from menu import menu
from backend.ingestion_utils import process_rfp_responses
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt

# Load environment variables from .env file
load_dotenv()

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
        MainMenu, header, footer, img[data-testid="stImage"], img[data-testid="stLogo"] {
            display: none;
        }
        .st-pagelink {
            color: #FFFFFF;
        }
        </style>
        """

# Applies the CSS Injection
st.markdown(new_style, unsafe_allow_html=True)

# Function to add a logo in Streamlit
def st_logo(image, size="small", link=None, icon_image=None):
    if size == "small":
        st.image(image, width=100)
    elif size == "medium":
        st.image(image, width=200)
    elif size == "large":
        st.image(image, width=300)
    if link is not None:
        st.markdown(f"[![Foo]({icon_image})]({link})")

# Load the logo image
image = Image.open('images/logo3.png')

# Display the menu in the sidebar
menu()

# Title alignment
title_alignment = """
<h1 style="font-size: 42px; text-align: center;">RFI/RFP Summary and Retooled Resume</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

# Initialize session state variables if not already initialized
if 'rfp_selection' not in st.session_state:
    st.session_state.rfp_selection = ''
if 'uploaded_response_files' not in st.session_state:
    st.session_state.uploaded_response_files = ''
if 'vendors_selected' not in st.session_state:
    st.session_state.vendors_selected = []
if 'reqs_selected' not in st.session_state:
    st.session_state.reqs_selected = []

# Display RFP Summary
st.markdown('<h3 style="text-align:center;">RFI/RFP Summary</h3>', unsafe_allow_html=True)
with st.container():
    st.markdown(st.session_state.rfp_document["content"].get("summary", "No summary available."))

# Display retooled resume if available in session state
if 'retooled_resume' in st.session_state:
    st.markdown('<h3 style="text-align:center;">Retooled Resume</h3>', unsafe_allow_html=True)
    with st.container():
        st.markdown(st.session_state.retooled_resume)

# Function to create a DOCX file from text
def create_docx(text, file_name):
    # Create a new Document
    doc = Document()
    # Add text to the Document
    doc.add_paragraph(text)
    # Save the Document to a BytesIO object
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)  # Move the cursor to the start of the stream
    return file_stream

# Check if 'retooled_resume' exists in session state
retooled_resume_text = st.session_state.get('retooled_resume', '')
if retooled_resume_text:
    # Create a docx file from the retooled resume text
    docx_file = create_docx(retooled_resume_text, "retooled_resume.docx")
    # Place the download button outside the form
    st.download_button(
        label="Download Retooled Resume",
        data=docx_file,
        file_name="retooled_resume.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# Run the application
if __name__ == '__main__':
    pass
