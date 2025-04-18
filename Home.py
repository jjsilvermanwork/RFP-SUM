import streamlit as st
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Please replace st.experimental_set_query_params with st.query_params")
warnings.filterwarnings("ignore", category=UserWarning, message="The use_column_width parameter has been deprecated")
warnings.filterwarnings("ignore", category=UserWarning, message="Please replace st.experimental_get_query_params with st.query_params")

from menu import menu

# Display the menu in the sidebar
menu()

# Get the current page from query parameters
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["Home"])[0]

if page == "Home":
    st.title("NTT DATA Internal Tools Suite")
    st.write("Welcome to the NTT DATA Internal Tools Suite. This suite includes tools to help you rapidly generate RFP responses and retool resumes. Use the sidebar to navigate between different tools.")
elif page == "RFP_Home":
    import pages.RFP_Home as RFP_Home
    RFP_Home.run()
elif page == "Resume_Retooler_Home":
    import pages.Resume_Retooler_Home as Resume_Retooler_Home
    Resume_Retooler_Home.run()
