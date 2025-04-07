import os
import streamlit as st
import time
from streamlit_pdf_viewer import pdf_viewer
from PIL import Image
from backend.ingestion_utils import logger, process_rfp_responses # needs to be commented out
from pages.menu import menu

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

# Custom CSS for sidebar and page background
background_color_html = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #FFFFFF;
    color: #2E404D;
}
"""

# Injecting the HTML code into the Streamlit app
st.markdown(background_color_html, unsafe_allow_html=True)

# Side Navigation Panel
image = Image.open('images/logo3.png')
st.logo(image, size="large", link=None, icon_image=None)

menu(True, True)

# Title
title_alignment = """
<h1 style="font-size: 42px; text-align: center;">RFI/RFP Summary</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)


if "vendors_selected" not in st.session_state:
    st.session_state["vendors_selected"] = []
if "reqs_selected" not in st.session_state:
    st.session_state["reqs_selected"] = []

vendor_list = st.session_state["vendors_selected"]
req_list = st.session_state["reqs_selected"]

if 'vendors_selected_filter' not in st.session_state:
    st.session_state['vendors_selected_filter'] = vendor_list

if 'requirements_selected_filter' not in st.session_state:
    st.session_state['requirements_selected_filter'] = req_list

if 'apply' not in st.session_state:
    st.session_state['apply'] = False
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 375px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:

    # st.markdown('### Filter')
    # with st.container(height=1000):
    #     vendors_selected_filter = st.multiselect(
    #             "Vendors",
    #             vendor_list,
    #             vendor_list
    #         )
            
    #     requirements_selected_filter = st.multiselect(
    #         "Requirements",
    #         req_list,
    #         req_list
    #         )
    col1, col2, col3 = st.columns([1, 20, 1])  # Adjust the ratios as needed
    # col1, col2 = st.columns([9, 1])  # Adjust the ratios as needed

    with col2:
        with st.container(height=950): #1000 og
            vendors_selected_filter = st.multiselect(
            "Vendors",
            vendor_list,
            vendor_list
            )
        
            requirements_selected_filter = st.multiselect(
            "Requirements",
            req_list,
            req_list
            )

if 'human notes' not in st.session_state:
    st.session_state[f'human notes'] = []

with st.form(f'Add notes below:'):
    human_notes = st.text_area('Working Notes: ', key=f'Human notes')
    sub_m = st.form_submit_button("Add note")
    if sub_m:
        st.session_state[f'human notes'].append(human_notes)
    st.info(str(st.session_state[f'human notes']).replace('[', '').replace(']', '').replace("'", ""))

# Creating an RFP requirement / RFP response answer dictionary for filter
try:
    if (st.session_state.get("rfp_reqs_response_answers") == None or st.session_state.get("rfp_reqs_response_answers") == []) or st.session_state.get("retry_loading") == True:
        st.session_state.retry_loading = False
        st.session_state.rfp_reqs_response_answers = []
        for idx, r in enumerate(req_list):
            rfp_response_answers = []
            for v in vendor_list:
                response_document = next((response for response in st.session_state.rfp_response_documents if response["document_name"] == v), None)
                answer = response_document["content"]["summary_list"][idx] 
                rfp_response_answer = {
                    "response_doc_name": v,
                    "requerment_answer": answer
                }
                rfp_response_answers.append(rfp_response_answer)

            rfp_reqs_response_answer = {
                "rfp_requirement": r,
                "rfp_response_docs_answers": rfp_response_answers
            }
            st.session_state.rfp_reqs_response_answers.append(rfp_reqs_response_answer)
            print(st.session_state.rfp_reqs_response_answers)

    if st.session_state.rfp_reqs_response_answers is not None or st.session_state.rfp_reqs_response_answers is not []:
        for idx, r in enumerate(requirements_selected_filter):
            st.markdown(f"##### {r}")
            for v in vendors_selected_filter:
                with st.container(border=True):
                    st.markdown(f"##### {v}")
                    with st.expander('Response Summary', expanded=True):
                        requirement = next((requirement for requirement in st.session_state.rfp_reqs_response_answers if requirement["rfp_requirement"] == r), None)
                        answer = next((answer["requerment_answer"] for answer in requirement["rfp_response_docs_answers"] if answer["response_doc_name"] == v), None)
                        if 'no supporting content' in answer.lower():
                            st.warning('No response found', icon="⚠️")
                        else:
                            st.markdown(answer)
                    with st.expander('Original Document'):
                        doc_path = os.path.join(st.session_state.SESSION_DIR, "responses", v)
                        pdf_viewer(doc_path, width=800, height=1000, key=f"pdf_{v}_{r}") # can add this argument to scroll to a specific page: scroll_to_page=3, 

except Exception as e:
    print(e)
    print(req_list)
    print("\n\n\n")
    print(len(st.session_state.rfp_response_documents))
    st.session_state.retry_loading = True
    process_rfp_responses(st)
    st.switch_page("pages/2_Summary.py")

with st.columns([9, 1])[1]:
    summarize = st.button("Chat", key=f'chat_with_all')
    # PROGRESS BAR CODE
    import time
    def progress_bar():
        progress_text = st.text("Gathering Requirements")
        progress_bar = st.progress(0)
        for percent_complete in range(0, 101, 10):
            time.sleep(0.1)
            progress_bar.progress(percent_complete)
            progress_text.text(f"{percent_complete}%")

    if summarize:
        # set summary true
        if "gen_summary" not in st.session_state:
            st.warning("Flag not initialized")
        else:
            st.session_state.gen_summary = True
            # st.success("Flag is now TRUE")
        # st.write("Flag Value: ", st.session_state.gen_summary)
        progress_bar()
        st.switch_page("pages/3_Chat.py")