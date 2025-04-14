import os
import time
import pandas as pd
import streamlit as st
from PIL import Image
from pages.menu import menu
from backend.ingestion_utils import process_rfp_responses
import requests
from dotenv import load_dotenv
import fitz  # PyMuPDF
import docx
import mammoth
import logging
import random  # Importing random module for exponential backoff with jitter
from docx import Document
from docx.shared import Pt
import io
from fpdf import FPDF

# Load environment variables from .env file
load_dotenv()

# OpenAI API settings
api_key = os.getenv('API_KEY')
endpoint = 'https://aiagentservice.openai.azure.com/openai/deployments/gpt-4-AIAgent-deploy/chat/completions?api-version=2024-02-15-preview'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}',
}

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
        position: fixed;
        }
        footer {
        visibility: hidden;
        height: 0%;
        position: fixed;
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

# Side Navigation Panel
image = Image.open('images/logo3.png')
st.logo(image, size="large", link=None, icon_image=None)

# Initialize session state for gen_summary if not already initialized
flag = st.session_state.get("gen_summary", None)

# Switches menu based on Flag
if flag is None:
    menu(True, False)
elif flag is True:
    menu(True, True)
else:
    menu(True, False)

title_alignment = """
<h1 style="font-size: 42px; text-align: center;">Summarized and Retooled Resume</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

if 'rfp_selection' not in st.session_state:
    st.session_state.rfp_selection = ''
if 'uploaded_response_files' not in st.session_state:
    st.session_state.uploaded_response_files = ''

if 'vendors_selected' not in st.session_state:
    st.session_state.vendors_selected = []
if 'reqs_selected' not in st.session_state:
    st.session_state.reqs_selected = []


# Display summarized and retooled resume if available in session state
if 'resume_summary' in st.session_state:
    st.markdown('<h3 style="text-align:center;">Resume Summary</h3>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(st.session_state.resume_summary)

if 'retooled_resume' in st.session_state:
    st.markdown('<h3 style="text-align:center;">Retooled Resume</h3>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(st.session_state.retooled_resume)

# Custom function to add a logo in Streamlit
def st_logo(image, size="small", link=None, icon_image=None):
    if size == "small":
        st.image(image, width=100)
    elif size == "medium":
        st.image(image, width=200)
    elif size == "large":
        st.image(image, width=300)
    if link is not None:
        st.markdown(f"[![Foo]({icon_image})]({link})")

# Placeholder for the `menu` function which should be defined in `pages/menu.py`
def menu(show_rfp, show_summary):
    if show_rfp:
        st.sidebar.markdown("Summarized and Retooled Resume")
    if show_summary:
        st.sidebar.markdown("Summary")

# Placeholder for the `process_rfp_responses` function which should be defined in `backend/ingestion_utils.py`
def process_rfp_responses(st):
    st.session_state.rfp_document = {
        "content": {"summary": "This is a summary of the RFP document."},
        "extracted_requirements": "Requirement 1\n\nRequirement 2\n\nRequirement 3"
    }

# Run the application
if __name__ == '__main__':
    pass
