import streamlit as st
import streamlit.components.v1 as components
import random
import time
from datetime import datetime
from PIL import Image
from backend.azure_resources_connections.aisearch_connector import rag_pipeline
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

now = datetime.now()
timestamp_ = str(now)

# Side Navigation Panel
image = Image.open('images/logo3.png')
st.logo(image, size="large", link=None, icon_image=None)

# needs to be initialized so that you can switch from requirements page to chat
if 'rfp_response_documents' not in st.session_state:
    st.session_state.rfp_response_documents = ''

# Initialize session state for gen_summary if not already initialized

flag = st.session_state.get("gen_summary", None)

if flag is None:
    # st.warning("Flag has not been initialized")
    menu(True, False)
elif flag is True:
    # st.success("The Flag is TRUE")
    menu(True, True)
else:
    # st.error("The Flag is FALSE")
    menu(True, False)

if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = {}
if 'current_conversation' not in st.session_state:
    st.session_state['current_conversation'] = ''

# Title
title_alignment = """
<h1 style="font-size: 42px; text-align: center;">RFI/RFP Chat</h1>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

old_chats = [k for k in st.session_state['conversation_history'].keys()]

# with st.columns([7, 2])[1]:
    # selected_chat = st.selectbox("Chat History", old_chats)

# n_chat = st.button('+ New Chat')
# if n_chat:
#     st.session_state['conversation_history'][timestamp_] = []
#     st.session_state['current_conversation'] = timestamp_

if len(st.session_state['current_conversation'])<1:
    st.session_state['conversation_history'][timestamp_] = []
    st.session_state['current_conversation'] = timestamp_

current_convo_key = st.session_state['current_conversation']
messages = st.session_state['conversation_history'][current_convo_key]

# Display chat messages from history on app rerun
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What do you want to know?"):
    # Add user message to chat history
    messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    response = rag_pipeline(prompt, messages)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    messages.append({"role": "assistant", "content": response})

st.session_state['conversation_history'][current_convo_key] = messages