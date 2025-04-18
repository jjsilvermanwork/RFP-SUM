import os
import time
import pandas as pd
import streamlit as st
from PIL import Image
from menu import menu
from backend.ingestion_utils import process_rfp_responses

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

# Side Navigation Panel
image = Image.open('images/logo3.png')
st.logo(image, size="large", link=None, icon_image=None)


# Initialize session state for gen_summary if not already initialized
flag = st.session_state.get("gen_summary", None)

# Switches menu based on Flag
if flag is None:
    # st.warning("Flag has not been initialized")
    menu(True, False)
elif flag is True:
    # st.success("The Flag is TRUE")
    menu(True, True)
else:
    # st.error("The Flag is FALSE")
    menu(True, False)

title_alignment = """
<h1 style="font-size: 42px; text-align: center;">RFI/RFP Requirements</h1>
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

st.markdown('<h3 style="text-align:center;">Summary</h3>', unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(st.session_state.rfp_document["content"].get("summary", None))

    # # This one is for testing without doing extraction process ___________
    # st.session_state.rfp_document = {}
    # st.session_state.rfp_document["content"] = {}
    # st.session_state.rfp_document["content"]["summary"] = "This is a test summary"
    # st.markdown(st.session_state.rfp_document["content"].get("summary", None))
    # # This one is for testing without doing extraction process ___________

st.markdown('<h3 style="text-align:center;">Requirements Extracted</h3>', unsafe_allow_html=True)


with st.container(border=True):
    # get RPF requirements we extracted

    requirements_extracted = st.session_state.rfp_document["extracted_requirements"].split('\n\n')


#     # This one is for testing without doing extraction process ___________
#     st.session_state.rfp_document["extracted_requirements"] = """1. Data Residency: All State data must remain in the United States, regardless of whether the data is processed, stored, in-transit, or at rest. Access to State data shall be limited to US-based (onshore) resources only.

# 2. Foreign Adversary Restriction: Software applications designed, developed, manufactured, or supplied by persons owned or controlled by, or subject to the jurisdiction or direction of, a foreign adversary (e.g., People's Republic of China) are prohibited.

# 3. Data Testing: Any testing of code outside of the United States must use fake data. A copy of production data may not be transmitted or used outside the United States.

# 4. Proof of Concept: The State may proceed to a Proof of Concept (POC) phase, allowing selected vendors to demonstrate the capabilities of their GenAI Procurement Tools in a real-world or simulated environment relevant to the State's procurement needs.

# 5. Experience Statement: Vendors must provide a statement about their experience providing similar scope of services/products to public entities, with public entity customers preferred.

# 6. AI/ML Expertise: Vendors must provide a summary of their experience in the AI/ML space, specifically with generative AI.

# 7. Team Expertise: Vendors must describe their team's expertise in procurement, contract law, and AI as it relates to public procurement.

# 8. Key Personnel: Vendors must provide details on the qualifications and experience of key personnel involved in the development and support of their GenAI procurement tools.

# 9. Customer References: Vendors must list 1-3 key customers currently using their GenAI procurement tools, with public entity customers preferred, and provide contact information if possible.

# 10. Contract Scope Assistance: Vendors must describe how their tool assists in defining, refining, and crafting clear and concise contract scopes, including support for templates, best practices, and industry standards, as well as identifying potential risks and ambiguities.

# 11. RFP Creation: Vendors must explain how their tool streamlines the RFP creation process, including assistance with creating technical questions and cost structures/methodologies for respondents.

# 12. Vendor Response Analysis: Vendors must describe how their tool helps analyze vendor RFP responses, including identifying key information, comparing bids, scoring proposals, and providing insights and recommendations to decision-makers.

# 13. AI/ML Models: Vendors must explain the specific AI/ML models and techniques used in their tools, including languages utilized (e.g., Natural Language Processing, Optical Character Recognition).

# 14. Accuracy and Efficiency: Vendors must describe how their tool enhances accuracy, efficiency, and decision-making in the procurement process.

# 15. Training Data: Vendors must describe the training data used for their AI models and how it ensures fairness, accuracy, and bias mitigation.

# 16. System Integration: Vendors must list existing procurement systems and platforms their tool integrates with (e.g., ERP, eProcurement platforms).

# 17. Deployment Model: Vendors must specify whether their solution is cloud-based, on-premise, or a hybrid model, and describe the deployment process, timelines, and customization/configuration options.

# 18. Training and Support: Vendors must describe the training and support services included in the solution, including ongoing support, maintenance, and service level agreements (SLAs) for response times and resolution.

# 19. Solution Uniqueness: Vendors must explain what makes their solution unique and innovative compared to competitors.

# 20. Future Development: Vendors must describe their plans for future development and enhancements to their GenAI procurement tools.

# 21. Implementation Timeline: Vendors must provide an estimated implementation timeline, including discovery, design, UAT testing, and go-live estimates, as well as resource and time commitment expectations for the State.

# 22. Security Measures: Vendors must describe the security measures their solution provides to ensure the security of confidential/sensitive State data, including encryption, security protocols, threat detection capabilities, and automated responses to detected threats.

# 23. Implementation Challenges: Vendors must identify potential challenges to implementing a GenAI procurement tool and suggest mitigation strategies.

# 24. Policy Compliance: Vendors must describe how they incorporate State policies and standards into their GenAI procurement solution.

# 25. Release Management: Vendors must describe their release management process for updates, maintenance, and customizations required for compliance with federal and state law, as well as their communication methods for maintenance, support, and system updates.

# 26. Cooperative Agreements: Vendors must specify through which public sector cooperative purchasing agreements they can provide their services (e.g., OMNIA, NASPO, GSA).

# 27. Additional Agreements: Vendors must list any additional agreements the State would need to sign to procure their solution (e.g., End User License Agreement) and provide a PDF version if applicable.

# 28. Proof of Concept Participation: Vendors must confirm their willingness to participate in a Proof of Concept (POC) phase, propose a timeframe for the POC, and indicate whether they would offer the POC at no cost to the State.

# 29. Pricing Model: Vendors must describe their pricing model (e.g., subscription, usage-based, perpetual license) and any tiered pricing options based on usage volume or features.

# 30. Implementation Costs: Vendors must describe the costs associated with implementation, training, and ongoing support, including services billed hourly/daily and typical hourly/daily rates by resource.

# 31. Licensing Terms: Vendors must specify any limitations on usage, data storage, or number of users in their licensing terms.

# 32. Alternative Approaches: Vendors must provide input on alternative approaches or additional considerations that might benefit the State."""
#     requirements_extracted = st.session_state.rfp_document["extracted_requirements"].split('\n\n')
#     # This one is for testing with doing extraction process ___________

    requirements_selected = []
    for req in requirements_extracted:
        req_select = st.checkbox(req, True)
        if req_select:
            requirements_selected.append(req)
            # code for adding it to file
            # Function to convert array to CSV

# Function to convert array to CSV for Export Requirements Button
def convert_to_csv(data):
    df = pd.DataFrame(data, columns=["Requirements"])
    return df.to_csv(index=False)

# Export Requirements Button
st.session_state.reqs_selected = requirements_selected
with st.columns([4, 1])[1]:
    csv = convert_to_csv(requirements_selected)
    st.download_button(
        label="Export Requirements",
        data=csv,
        file_name="requirements.csv",
        mime="text/csv")

# get RFP responses file names
rfp_responses_directory = os.path.join(st.session_state.SESSION_DIR, "responses")
total_vendors = [f for f in os.listdir(rfp_responses_directory) if os.path.isfile(os.path.join(rfp_responses_directory, f))]
st.markdown('<h3 style="text-align:center;">Vendor Selection</h3>', unsafe_allow_html=True)
st.write('Select vendors to compare.')
vendors_selected = []
with st.container(border=True):
    for i in total_vendors:
        vend_select = st.checkbox(i, True)
        if vend_select:
            vendors_selected.append(i)

st.session_state.vendors_selected = vendors_selected

with st.columns([5.25, 1])[1]:
    summarize = st.button("Summarize")

    if summarize:
        process_rfp_responses(st)
        # set summary true
        if "gen_summary" not in st.session_state:
            st.warning("Flag not initialized")
        else:
            st.session_state.gen_summary = True
            st.success("Flag is now TRUE")
        st.write("Flag Value: ", st.session_state.gen_summary)
        st.switch_page("pages/Summary.py")


