import streamlit as st
import time
from backend.ingestion_utils import upload_pdf_extract_reqs  # This needs to be commented out if testing locally without backend
from PIL import Image
from pages.menu import menu  # What is visible on the side bar prior to document submission
import io
from io import BytesIO
import fitz  # PyMuPDF
import docx
import mammoth
import requests
import logging
import random  # Importing random module for exponential backoff with jitter
import os
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv
from fpdf import FPDF
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# Load environment variables from .env file
load_dotenv()

# OpenAI API settings
api_key = os.getenv('API_KEY')
endpoint = 'https://aiagentservice.openai.azure.com/openai/deployments/gpt-4-AIAgent-deploy/chat/completions?api-version=2024-02-15-preview'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}',
}

# Functions for reading files and creating DOCX
def read_pdf(file):
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def read_doc(file):
    result = mammoth.convert_to_html(file)
    text = result.value  # The generated HTML
    return text

def summarize_resume(resume_content):
    data = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant that summarizes resumes in paragraph format and ensures the summary ends on a complete thought."},
            {"role": "user", "content": f"Resume:\n{resume_content}\n\nPlease provide a summary of the above resume in paragraph format and ensure it ends on a complete thought."}
        ],
        "max_tokens": 300  # Increased limit
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, verify=False)  # SSL verification disabled here
        response.raise_for_status()
        result = response.json()
        summary = result['choices'][0]['message']['content'].strip()
        
        # Ensure the summary ends on a complete thought
        if summary.endswith("...") or summary.endswith(",") or summary.endswith("and"):
            data["messages"].append({"role": "user", "content": "Please finish the summary to ensure it ends on a complete thought."})
            response = requests.post(endpoint, headers=headers, json=data, verify=False)
            response.raise_for_status()
            result = response.json()
            continuation = result['choices'][0]['message']['content'].strip()
            summary += " " + continuation
        
        return summary
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception occurred: {e}")
        return f"An error occurred: {e}"
    except KeyError:
        logging.error("Unexpected response format.")
        return "Unexpected response format."

def extract_skills_from_requirements(rfp_requirements):
    data = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant that extracts hard and soft skills from RFI/RFP requirements."},
            {"role": "user", "content": f"RFP Requirements:\n{rfp_requirements}\n\nPlease extract the hard skills and soft skills mentioned in the requirements."}
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, verify=False)
        response.raise_for_status()
        result = response.json()
        extracted_skills = result['choices'][0]['message']['content'].strip()
        return extracted_skills
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception occurred: {e}")
        return f"An error occurred: {e}"
    except KeyError:
        logging.error("Unexpected response format.")
        return "Unexpected response format."

def retool_resume(resume_content, rfp_summary, extracted_skills):
    data = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant that retools resumes to match RFI/RFP summaries and extracted skills."},
            {"role": "user", "content": f"Resume:\n{resume_content}\n\nRFP Summary:\n{rfp_summary}\n\nExtracted Skills:\n{extracted_skills}\n\nPlease retool the resume to better match the RFP summary and skills, and format it with only the following sections: Header, Professional Biography, Skills Summary, Highlights, and Key Experiences. I want the end of the retooled resume to be at the end of the Key Experiences section."}
        ],
        "max_tokens": 1000  # Adjust as needed
    }

    retries = 3  # Number of retries
    for attempt in range(retries):
        try:
            response = requests.post(endpoint, headers=headers, json=data, verify=False)  # SSL verification disabled here
            response.raise_for_status()
            result = response.json()
            retooled_resume = result['choices'][0]['message']['content'].strip()
            
            if retooled_resume.endswith("..."):  # Check if the response is truncated
                data["messages"].append({"role": "user", "content": "Please continue retooling the resume."})
                response = requests.post(endpoint, headers=headers, json=data, verify=False)
                response.raise_for_status()
                result = response.json()
                continuation = result['choices'][0]['message']['content'].strip()
                retooled_resume += " " + continuation
            
            return retooled_resume
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception occurred: {e}")
            if attempt < retries - 1:  # if not the last attempt
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                logging.info(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                return f"An error occurred: {e}"
        except KeyError:
            logging.error("Unexpected response format.")
            return "Unexpected response format."



def create_docx_from_text(text, filename="Retooled_Resume.docx"):
    doc = Document()
    
    # Split the text into sections
    sections = text.split('\n\n')
    for section in sections:
        if section.startswith('Header'):
            # Add Header
            header_lines = section.split('\n')
            for line in header_lines[1:]:
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(14)
                run.font.bold = True
                run.font.name = 'Arial'
        elif section.startswith('Professional Biography'):
            # Add Professional Biography
            paragraph = doc.add_paragraph()
            run = paragraph.add_run('Professional Biography')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.name = 'Arial'
            run.font.underline = True
            bio_lines = section.split('\n')[1:]
            for line in bio_lines:
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(12)
                run.font.name = 'Arial'
        elif section.startswith('Skills Summary'):
            # Add Skills Summary
            paragraph = doc.add_paragraph()
            run = paragraph.add_run('Skills Summary')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.name = 'Arial'
            run.font.underline = True
            skills_lines = section.split('\n')[1:]
            for line in skills_lines:
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(12)
                run.font.name = 'Arial'
        elif section.startswith('Highlights'):
            # Add Highlights
            paragraph = doc.add_paragraph()
            run = paragraph.add_run('Highlights')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.name = 'Arial'
            run.font.underline = True
            highlights_lines = section.split('\n')[1:]
            for line in highlights_lines:
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(12)
                run.font.name = 'Arial'
        elif section.startswith('Key Experiences'):
            # Add Key Experiences
            paragraph = doc.add_paragraph()
            run = paragraph.add_run('Key Experiences')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.name = 'Arial'
            run.font.underline = True
            experiences_lines = section.split('\n')[1:]
            for line in experiences_lines:
                paragraph = doc.add_paragraph()
                run = paragraph.add_run(line)
                run.font.size = Pt(12)
                run.font.name = 'Arial'
        else:
            # Add any other sections
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(section)
            run.font.size = Pt(12)
            run.font.name = 'Arial'

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

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
        st.sidebar.markdown("RFP Requirements")
    if show_summary:
        st.sidebar.markdown("Summary")

# Placeholder for the `process_rfp_responses` function which should be defined in `backend/ingestion_utils.py`
def process_rfp_responses(st):
    st.session_state.rfp_document = {
        "content": {"summary": "This is a summary of the RFP document."},
        "extracted_requirements": "Requirement 1\n\nRequirement 2\n\nRequirement 3"
    }

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
<h1 style="font-size: 42px; text-align: center;">NTT DATA Resume Retooler</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

if 'rfp_selection' not in st.session_state:
    st.session_state.rfp_selection = ''
if 'uploaded_response_files' not in st.session_state:
    st.session_state.uploaded_response_files = ''

with st.form('file_selection'):
    st.markdown('Upload *pdf files* for the proposal and resume below:')
    rfp_selection = st.file_uploader('Upload the original RFI/RFP file', type=['pdf'])
    st.session_state.rfp_selection = rfp_selection
    
    # Add the upload resume section
    resume_file = st.file_uploader("Upload your Resume", type=['pdf', 'doc', 'docx'])
    st.session_state.resume_file = resume_file

    with st.columns([4, 1])[1]:
        submitted = st.form_submit_button("Retool Resume", use_container_width=True)

        if submitted:
            upload_pdf_extract_reqs(st)
            # Process the resume file and generate a summary
            if 'resume_file' in st.session_state and st.session_state.resume_file:
                resume_content = ""
                if st.session_state.resume_file.type == "application/pdf":
                    st.write("Reading PDF resume...")
                    resume_content = read_pdf(st.session_state.resume_file)
                elif st.session_state.resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    st.write("Reading DOCX resume...")
                    resume_content = read_docx(st.session_state.resume_file)
                elif st.session_state.resume_file.type == "application/msword":
                    st.write("Reading DOC resume...")
                    resume_content = read_doc(st.session_state.resume_file)

                if resume_content:
                    st.write("Resume content read successfully.")
                    summary = summarize_resume(resume_content)
                    st.session_state.resume_summary = summary  # Store summary in session state

                    # Extract skills from RFP requirements
                    rfp_requirements = "\n".join(st.session_state.get('reqs_selected', []))
                    extracted_skills = extract_skills_from_requirements(rfp_requirements)

                    # Retool the resume based on RFP summary and extracted skills
                    rfp_summary = st.session_state.rfp_document["content"].get("summary", "")
                    retooled_resume = retool_resume(resume_content, rfp_summary, extracted_skills)
                    st.session_state.retooled_resume = retooled_resume  # Store retooled resume in session state

                    # Create DOCX file for download
                    #docx_buffer = create_docx_from_text(retooled_resume)
        
                    # Add download button for the retooled resume
                    #st.download_button(
                    #    label="Download Retooled Resume",
                    #    data=docx_buffer,
                    #    file_name="Retooled_Resume.docx",
                    #    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    #)
                #else:
                    #st.error("Failed to read the resume content. Please check the file format.")

                    st.switch_page("pages/1_RFP_Requirements.py")

# Run the application
if __name__ == '__main__':
    pass
           

