import streamlit as st
from PIL import Image
    
def menu(is_uploaded, is_summarized):
   
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
    # st.success("Flag initialized to FALSE")
    # else:
    #     st.info(f"Flag already exists: {st.session_state.gen_summary}")

    image = Image.open('images/logo3.png')
    # Use logo for Side Panel
    st.logo(image, size="large", link=None, icon_image=None)

    # Determine what pages are available on the side panel, bas.geed on the logic of what is uploaded
    if is_uploaded == False and is_summarized == False: # Start at Home Page
        st.sidebar.page_link("./Home.py", label = "Home")

    elif is_uploaded == True and is_summarized == False: # Before Requirements uploaded
        st.sidebar.page_link("./Home.py", label = "Return Home")
        st.sidebar.page_link("./pages/1_RFP_Requirements.py", label = "Resume Retooling")

    elif is_uploaded == True and is_summarized == True: # After requirements uploaded
        st.sidebar.page_link("./Home.py", label = "Return Home")
        st.sidebar.page_link("./pages/1_RFP_Requirements.py", label = "Resume Retooling")
