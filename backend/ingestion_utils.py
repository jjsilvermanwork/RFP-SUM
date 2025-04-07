import os
import time
import concurrent.futures
from datetime import datetime
import uuid
from dotenv import load_dotenv
import tiktoken
from backend.azure_resources_connections.openai_connector import create_embeddings_for_document, openai_4o_client, openai_o1_mini_client
from azure.ai.documentintelligence.models import DocumentContentFormat
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzedDocument, DocumentContentFormat

from backend.azure_resources_connections.aisearch_connector import aisearch_client, upload_documents_to_aisearch
from backend.prompts.prompt_configs import (
    combine_requirements_prompt,
    combine_summaries_prompt,
    compare_documents_prompt,
    generate_requirements_prompt,
    generate_rfp_summary_prompt,
    summarize_chunk_prompt
)
from backend.azure_resources_connections.documentintelligence_connector import chunk_on_md, pdf_to_md, document_intelligence_client


# Load environment variables from .env file.
load_dotenv()


def count_tokens(text, model_name="gpt-3.5-turbo"):
    """
    Count tokens using tiktoken.
    """
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(text))


class Logger:
    """
    Logger class for managing two sets of logs:
      - overall_log: for high-level process events.
      - detailed_log: for every LLM call (prompts and responses).

    When an instance is created, an output directory is immediately generated using a timestamp.
    Every call to save_log_file saves a file in that directory with a file name based on the provided
    method_name (without appending a timestamp to the file name).
    After saving, the logs are cleared.
    """
    def __init__(self):
        self.overall_log = ""   # High-level process messages.
        self.detailed_log = ""  # Detailed LLM call logs.
        
        # Create a unique output folder at instantiation time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join("backend", "run logs", f"run_{timestamp}")
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Output directory created: {self.output_dir}")
    
    def log_overall(self, message):
        """
        Append a message to the overall log.
        """
        self.overall_log += f"\n{message}"
    
    def log_detailed(self, step_name, prompt, output, newline_count):
        """
        Append detailed logging info for a particular step.
        """

        prompt_tokens = count_tokens(prompt)
        output_tokens = count_tokens(output)
        
        entry = (
            f"\n## {step_name}\n"
            f"### Prompt:\n```{prompt} \n\n[TOKENS: {prompt_tokens}]\n```\n"
            f"### Output:\n```{output}\n\n[NEWLINE COUNT: {newline_count}] \n\n[TOKENS: {output_tokens}]\n```\n"
        )
        self.detailed_log += entry
        print(f"Logged step: {step_name}")
    
    def save_requirements_log_file(self, start_time=None):
        """
        Save the overall and detailed logs into a Markdown file in the output directory.
        The file is named "{method_name}_log.md" without a timestamp on the file name.
        Optionally compute and log additional metadata if start_time and/or total_reqs are provided.
        After saving, the logs are cleared.

        Parameters:
          method_name (str): Identifier to include in the file name.
          start_time (float, optional): The timestamp at the beginning of the process to compute total time.
          total_reqs (list, optional): A list of numerical requirements to log extra metrics.
        """
        # Optionally, log processing time
        if start_time is not None:
            total_time = time.time() - start_time
            self.log_overall("# Run Metadata")
            self.log_overall(f"Total Processing Time: {total_time:.2f} seconds")

        total_tokens = count_tokens(logger.overall_log + "\n" + logger.detailed_log)
        logger.log_overall(f"Total Token Count (not including reasoning): {total_tokens}")

        # Optionally, log details from total_reqs
        if total_reqs is not None:
            self.log_overall(f"Total requirements: {total_reqs}")
            if len(total_reqs) > 2:
                sorted_numbers = sorted(total_reqs)
                differences = [
                    abs(sorted_numbers[i+1] - sorted_numbers[i])
                    for i in range(len(sorted_numbers)-1)
                ]
                total_reqs_dif = sum(differences) / len(differences)
                self.log_overall(f"Total requirements average difference: {total_reqs_dif}")
            self.log_overall(f"Total requirements distance range: {max(total_reqs) - min(total_reqs)}")

        # Save the log file in the pre-created output directory
        file_name = f"requirements_log.md"
        output_path = os.path.join(self.output_dir, file_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# LLM Process Log\n")
            f.write(self.overall_log)
            f.write("\n")
            f.write(self.detailed_log)
        
        print(f"Log file saved to: {output_path}")

        # Clear the logs after saving
        self.overall_log = ""
        self.detailed_log = ""

    def save_summary_log_file(self, start_time=None):
        """
        Save the overall and detailed logs into a Markdown file in the output directory.
        The file is named "{method_name}_log.md" without a timestamp on the file name.
        Optionally compute and log additional metadata if start_time and/or total_reqs are provided.
        After saving, the logs are cleared.

        Parameters:
          method_name (str): Identifier to include in the file name.
          start_time (float, optional): The timestamp at the beginning of the process to compute total time.
          total_reqs (list, optional): A list of numerical requirements to log extra metrics.
        """
        # Optionally, log processing time
        if start_time is not None:
            total_time = time.time() - start_time
            self.log_overall("# Run Metadata")
            self.log_overall(f"Total Processing Time: {total_time:.2f} seconds")
        
        total_tokens = count_tokens(logger.overall_log + "\n" + logger.detailed_log)
        logger.log_overall(f"Total Token Count (not including reasoning): {total_tokens}")


        # Save the log file in the pre-created output directory
        file_name = f"summary_log.md"
        output_path = os.path.join(self.output_dir, file_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# LLM Process Log\n")
            f.write(self.overall_log)
            f.write("\n")
            f.write(self.detailed_log)
        
        print(f"Log file saved to: {output_path}")

        # Clear the logs after saving
        self.overall_log = ""
        self.detailed_log = ""


# Global logger instance
logger = Logger()

global total_reqs
total_reqs = []

def upload_pdf_files(rfp_doc, rfp_response_docs):
    """ Uploads both the RFP and the RFP Response documents chosen in the UI"""
    # get absolute path to uploaded_RFP_docs folder
    upload_RFP_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../backend/uploaded_RFP_docs'))
    # create new session folder for these uploadeds with datetime name 
    timestamp = datetime.now().strftime("%Y-%m%d_%H-%M-%S")
    SESSION_DIR = os.path.join(upload_RFP_file_path, timestamp)

    RFP_DIR = os.path.join(SESSION_DIR, "RFP")
    RESPONSES_DIR = os.path.join(SESSION_DIR, "responses")

    os.makedirs(RFP_DIR, exist_ok=True)
    os.makedirs(RESPONSES_DIR, exist_ok=True)

    # upload RFP document 
    RFP_DIR_FILEPATH = os.path.join(RFP_DIR, rfp_doc.name)
    with open(RFP_DIR_FILEPATH, "wb") as f:
        f.write(rfp_doc.getbuffer())

    # upload RFP response documents
    for file in rfp_response_docs:
        RESPONSES_DIR_FILEPATH = os.path.join(RESPONSES_DIR, file.name)
        with open(RESPONSES_DIR_FILEPATH, "wb") as f:
            f.write(file.getbuffer())
    return SESSION_DIR


def call_openai(prompt, step_name=""):
    AZURE_DEPLOYMENT_NAME_o1_MINI = os.getenv("AZURE_DEPLOYMENT_NAME_o1_MINI")
    AZURE_DEPLOYMENT_NAME_4o = os.getenv("AZURE_DEPLOYMENT_NAME_4o")

    # response = openai_o1_mini_client.chat.completions.create(
    #     model=AZURE_DEPLOYMENT_NAME_o1_MINI,
    #     messages=[{"role": "user", "content": prompt}],
    # )

    response = openai_4o_client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME_4o,
        messages=[{"role": "user", "content": prompt}],
        temperature=.3,
        top_p=.3,
    )
    output = response.choices[0].message.content  # Access output as a field.
    # Count the number of newline characters in the output.
    newline_count = output.count('\n')
    total_reqs.append(newline_count)
    # Append the newline count information to the prompt for logging.
    # This creates a new version of the prompt that includes the newline count.
    prompt_with_newlines = f"{output}\n\n[NEWLINE COUNT: {newline_count}]"

    # If a step name is provided, log the detailed information.
    if step_name:
        logger.log_detailed(step_name, prompt, output, prompt_with_newlines)
    return output

# ----------------------------------------
# Word-based chunking function.
# Splits a document into chunks of approximately 'chunk_size' words,
# with an overlap of 'overlap' words between chunks.
# ----------------------------------------
def chunk_document(document, chunk_size, overlap=50):
    words = document.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # Overlap words for next chunk.
    return chunks

# ----------------------------------------
# Process requirements extraction for the RFP document.
# Updates the global logger (logger.overall_log) directly.
# ----------------------------------------
def process_requirements(pdf_in_md, doc_title, chunk_size, overlap):
    logger.log_overall(f"# Processing Requirements for {doc_title}")
    # chunck the PDF based on word count chunck size
    chunks = chunk_document(pdf_in_md, chunk_size, overlap)
    logger.log_overall(f"Document divided into {len(chunks)} chunks.")
    dynamic_req_outputs = []
    rfp_summary = ""
    previous_requirements_accumulated = ""
    # Generate requirements for each chunck
    for idx, chunk in enumerate(chunks):
        prompt = generate_requirements_prompt(chunk, previous_requirements_accumulated)
        step_name = f"{doc_title} - Requirements for Chunk {idx+1}"
        req_response = call_openai(prompt, step_name=step_name)
        dynamic_req_outputs.append(req_response)
        previous_requirements_accumulated += "\n" + req_response
        logger.log_overall(f"Chunk {idx+1} requirements generated.")

        
    # Genrate RFP summary
    rfp_summary_prompt = generate_rfp_summary_prompt(chunks[0])
    rfp_summary = call_openai(rfp_summary_prompt)
    return chunks, dynamic_req_outputs, rfp_summary

# ----------------------------------------
# Process summarization for a single document.
# Splits the document into chunks, processes each chunk concurrently,
# and then combines the chunk summaries.
# Updates the global logger directly.
# ----------------------------------------
def process_document_summarization(doc_title, doc_text, chunk_size, overlap, refined_requirements):
    logger.log_overall(f"# Processing Summarization for {doc_title}")
    chunks = chunk_document(doc_text, chunk_size, overlap)
    logger.log_overall(f"Document divided into {len(chunks)} chunks.")
    chunk_summaries = [None] * len(chunks)
   
    def summarize_chunk(idx, chunk):
        return idx, call_openai(summarize_chunk_prompt(chunk, refined_requirements),
                                  step_name=f"{doc_title} - Summarize Chunk {idx+1}")
   
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(summarize_chunk, idx, chunk) for idx, chunk in enumerate(chunks)]
        for future in concurrent.futures.as_completed(futures):
            idx, summary = future.result()
            chunk_summaries[idx] = summary
            logger.log_overall(f"Chunk {idx+1} summary generated.")
   
    # Combine all the chunks
    combine_prompt = combine_summaries_prompt(chunk_summaries, refined_requirements)
    final_summary = call_openai(combine_prompt, step_name=f"{doc_title} - Combine Summaries")
    logger.log_overall(f"Final summary for {doc_title} generated.")
    return final_summary


# ----------------------------------------
# Compare 2 summaries with an llm call 
# ----------------------------------------
def compare_summaries(final_summaries, global_refined_requirements):
        titles = list(final_summaries.keys())
        summary_a = final_summaries[titles[0]]
        summary_b = final_summaries[titles[1]]
        compare_prompt_str = compare_documents_prompt(summary_a, summary_b, global_refined_requirements)
        comparative_summary = call_openai(compare_prompt_str, step_name="Compare Documents")
        logger.log_overall("# Processing summary generation.")
        logger.log_overall("Comparative summary generated.")
        print("----- COMPARATIVE SUMMARY -----")
        print(comparative_summary)







# ----------------------------------------
# Upload PDF files and extract requiremetns 
# ----------------------------------------
def upload_pdf_extract_reqs(st):

    def update_progress_bar(percent_complete, progress_text):
        progress_bar.progress(percent_complete)
        progress_label.text = (f"{progress_text}%")

    start_time = time.time()
    # Initial progress bar
    progress_label = st.text("Gathering Requirements...")
    progress_bar = st.progress(0)
    
    # ---------------------
    # Upload PDF files
    # ---------------------
    if st.session_state.rfp_selection:
        st.session_state.SESSION_DIR = upload_pdf_files(st.session_state.rfp_selection, st.session_state.uploaded_response_files)
    else:
        # TODO: update this to throw error to UI
        print("Throw error")

    # ---------------------
    # convert RFP PDF to MarkDown
    # ---------------------
    update_progress_bar(25, "Gathering Requirements...")
    pdf_in_md = pdf_to_md(st.session_state.SESSION_DIR, "RFP", st.session_state.rfp_selection.name)

    # ---------------------
    # Index MD RFP in AI Search
    # ---------------------
    update_progress_bar(50, "Gathering Requirements...")

    doc_id = str(uuid.uuid4())
    md_chuncks = chunk_on_md(pdf_in_md, doc_id)
    st.session_state.rfp_document = {
        "document_name": st.session_state.rfp_selection.name,
        "document_id": doc_id,
        "content": {
            "pdf_md": pdf_in_md,
            "chunks": md_chuncks,
            "summary": ""
        },
        "extracted_requirements": ""
    }
    create_embeddings_for_document(st.session_state.rfp_document)
    rfp_documents = [st.session_state.rfp_document]
    upload_documents_to_aisearch(rfp_documents)


    # ---------------------
    # Extract RFP requirements and generate RFP summary
    # ---------------------
    update_progress_bar(75, "Extracting RFP Requirements")

    chunk_size = 1600  # words per chunk.
    overlap = 50       # words overlap.

    rfp_chunks, rfp_dynamic_reqs, rfp_summary = process_requirements(pdf_in_md, "RFP Document", chunk_size, overlap)

    # Combine dynamic requirements from the RFP into global refined requirements.
    combine_req_prompt_text = combine_requirements_prompt(rfp_dynamic_reqs)
    st.session_state.rfp_document["extracted_requirements"] = call_openai(combine_req_prompt_text, step_name="Combine Requirements from RFP Document")
    st.session_state.rfp_document["content"]["summary"] = rfp_summary 
    logger.log_overall("Global refined summarization requirements generated from RFP document.")
    

    logger.save_requirements_log_file(start_time=start_time)


# ----------------------------------------
# Process the uploaded RFP Responses based on extracted requirements
# ----------------------------------------
def process_rfp_responses(st):

    def update_progress_bar(percent_complete, progress_text):
        progress_bar.progress(percent_complete)
        progress_label.text = (f"{progress_text}%")

    start_time = time.time()
    # Initial progress bar
    progress_label = st.text("Summarizing documents...")
    progress_bar = st.progress(0)

    # ---------------------
    # convert RFP Responses PDF to MarkDown
    # ---------------------
    update_progress_bar(10, "Converting PDFs")
    responses_in_md = []
    for vendor in st.session_state.vendors_selected:
        response = {
            "file_name": vendor,
            "md_content": pdf_to_md(st.session_state.SESSION_DIR, "responses", vendor)
        }
        responses_in_md.append(response)

    # ---------------------
    # Index MD RFP Responses in AI Search
    # ---------------------
    update_progress_bar(25, "Processing")
    st.session_state.rfp_response_documents = []

    for response in responses_in_md:
        doc_id = str(uuid.uuid4())
        md_chuncks = chunk_on_md(response["md_content"], doc_id)

        rdp_response_document = {
            "document_name": response["file_name"],
            "document_id": doc_id,
            "content": {
                "pdf_md": response["md_content"],
                "chunks": md_chuncks,
                "summary": "",
                "summary_list": []
            }
        }

        create_embeddings_for_document(rdp_response_document)
        rfp_documents = [rdp_response_document]
        upload_documents_to_aisearch(rfp_documents)

        st.session_state.rfp_response_documents.append(rdp_response_document)

    # ---------------------
    # Summarize documents based on extracted requirements
    # ---------------------
    update_progress_bar(50, "Summarizing Vendor Responses")

    for response in st.session_state.rfp_response_documents:

        chunk_size = 1600  # words per chunk.
        overlap = 50  
        response["content"]["summary"] = process_document_summarization(response["document_name"], response["content"]["pdf_md"], chunk_size, overlap, st.session_state.rfp_document["extracted_requirements"])
        response["content"]["summary_list"] = response["content"]["summary"].split('\n\n')
    print("test")

    logger.save_summary_log_file(start_time=start_time)


    # # ---------------------
    # # This is for hardcoded testing only
    # # ---------------------
    # st.session_state.rfp_response_documents = []
    # summary_1 = """'1. Data Residency: All data is processed and stored within the U.S. to comply with state data residency requirements.\n\n2. Foreign Adversary Restriction: No supporting specifications found.\n\n3. Data Testing: No supporting specifications found.\n\n4. Proof of Concept: The proposal includes a POC phase with a duration of 30 to 45 days, offered at no cost to the State, focusing on contract optimization and RFP drafting efficiency.\n\n5. Experience Statement: Innovative GenAI Solutions Inc. has over a decade of experience in AI-driven applications for public sector clients.\n\n6. AI/ML Expertise: The company specializes in building next-generation AI applications and employs technologies such as Natural Language Processing (NLP) and Machine Learning models for pattern recognition and predictive analytics.\n\n7. Team Expertise: The team comprises experts in AI/ML, public procurement, and cybersecurity, ensuring solutions meet high standards of performance and security.\n\n8. Key Personnel: Key personnel include Alex Rivera, Chief Innovation Officer, with contact details provided.\n\n9. Customer References: No supporting specifications found.\n\n10. Contract Scope Assistance: The tool assists with intelligent template selection, risk detection, and customization of templates to incorporate state-specific nuances.\n\n11. RFP Creation: The platform produces initial drafts of RFP documents using generative AI, including technical queries and structured cost frameworks, and provides process guidance based on best practices.\n\n12. Vendor Response Analysis: The solution analyzes vendor proposals to extract key performance indicators, quantifies risk and value, and generates visual scorecards and analytical reports.\n\n13. AI/ML Models: The solution employs Natural Language Processing (NLP) for document analysis and text generation, and Optical Character Recognition (OCR) for legacy document integration.\n\n14. Accuracy and Efficiency: The solution is designed to optimize contract language, streamline RFP creation, and provide deep analytics on vendor proposals, ensuring efficiency and improved accuracy.\n\n15. Training Data: No supporting specifications found.\n\n16. System Integration: The solution integrates with ERP, financial, and eProcurement systems using RESTful APIs.\n\n17. Deployment Model: The solution is primarily cloud-based, hosted on secure U.S.-based servers, with a hybrid deployment option available. The implementation timeline is 10-12 weeks.\n\n18. Training and Support: Comprehensive onboarding sessions, on-site and virtual training, extensive user documentation, round-the-clock support, and defined SLAs are included.\n\n19. Solution Uniqueness: No supporting specifications found.\n\n20. Future Development: Planned upgrades include enhancements to analytics modules, real-time reporting, and expanded integration features.\n\n21. Implementation Timeline: Typical engagements adopt a 10-12 week cycle covering discovery, design, testing (UAT), and deployment.\n\n22. Security Measures: The solution incorporates state-of-the-art encryption protocols for data at rest and in transit, supplemented by real-time threat monitoring systems.\n\n23. Implementation Challenges: No supporting specifications found.\n\n24. Policy Compliance: The solution ensures robust compliance with state data policies and adheres to all relevant federal and state security standards.\n\n25. Release Management: No supporting specifications found.\n\n26. Cooperative Agreements: No supporting specifications found.\n\n27. Additional Agreements: No supporting specifications found.\n\n28. Proof of Concept Participation: The proposal confirms willingness to participate in a POC phase, with a duration of 30 to 45 days, offered at no cost to the State.\n\n29. Pricing Model: The solution is offered under a subscription model with tiered pricing based on usage volume and required modules.\n\n30. Implementation Costs: Implementation, training, and initial support are bundled into a fixed cost package, with additional consulting available on an hourly basis.\n\n31. Licensing Terms: Flexible licensing agreements are provided to meet the scale and specific needs of the State.\n\n32. Alternative Approaches: No supporting specifications found.'"""
    # rdp_response_document_2 = {
    #     "document_name": "rfi_response_2.pdf",
    #     "document_id": "1234",
    #     "content": {
    #         "pdf_md": "",
    #         "chunks": "",
    #         "summary": summary_1
    #     }
    # }
    # rdp_response_document_2["content"]["summary_list"] = rdp_response_document_2["content"]["summary"].split('\n\n')
    # summary_2 = """"1. Data Residency: All processing and storage is confined to United States-based facilities, ensuring strict adherence to state security and sovereignty policies.\n\n2. Foreign Adversary Restriction: No supporting specifications found.\n\n3. Data Testing: No supporting specifications found.\n\n4. Proof of Concept: Precision AI Solutions is prepared to participate in a POC phase with a proposed duration of 45 days at no cost to the State, focusing on contract refinement and RFP drafting capabilities.\n\n5. Experience Statement: Precision AI Solutions has over eight years of experience integrating AI into government and public sector processes, including implementing AI-driven systems for contract scope refinement, RFP creation, and vendor evaluation.\n\n6. AI/ML Expertise: Precision AI Solutions employs advanced Natural Language Processing and machine learning algorithms for procurement processes.\n\n7. Team Expertise: The team combines expertise in AI/ML, public procurement strategies, and data security protocols.\n\n8. Key Personnel: Morgan Lee, VP of Product Development, is listed as the primary contact, but no further details on key personnel qualifications are provided.\n\n9. Customer References: No supporting specifications found.\n\n10. Contract Scope Assistance: The generative AI tool assists in refining contract documents using industry-standard templates, highlighting potential ambiguities and risks, and suggesting iterative improvements.\n\n11. RFP Creation: The tool automates parts of the RFP drafting process by generating initial drafts, recommending technical questions, and offering customizable cost-structure frameworks.\n\n12. Vendor Response Analysis: The tool parses procurement documentation, identifies key parameters and metrics, and supports Optical Character Recognition (OCR) for legacy document processing.\n\n13. AI/ML Models: The solution employs advanced Natural Language Processing and machine learning algorithms, with OCR capabilities for legacy documents.\n\n14. Accuracy and Efficiency: No supporting specifications found.\n\n15. Training Data: No supporting specifications found.\n\n16. System Integration: The platform integrates with common ERP and eProcurement systems via RESTful APIs.\n\n17. Deployment Model: The solution is cloud-based, hosted on U.S. servers, with hybrid configurations supported. Implementation follows a 10-14 week timeline, including discovery, design, UAT, and go-live phases.\n\n18. Training and Support: A comprehensive onboarding program includes user training sessions, detailed documentation, and access to a 24/7 support portal. Ongoing support includes proactive maintenance, regular updates, and a responsive technical support team with defined SLAs.\n\n19. Solution Uniqueness: No supporting specifications found.\n\n20. Future Development: The roadmap includes deeper analytics, real-time decision support, integration with emerging procurement platforms, and enhanced predictive analytics features.\n\n21. Implementation Timeline: Implementation typically follows a 10-14 week timeline, including discovery, design, UAT, and go-live phases.\n\n22. Security Measures: The solution uses industry-standard encryption for data at rest and in transit, continuous monitoring for threats, and automated alerts for rapid response.\n\n23. Implementation Challenges: No supporting specifications found.\n\n24. Policy Compliance: No supporting specifications found.\n\n25. Release Management: No supporting specifications found.\n\n26. Cooperative Agreements: No supporting specifications found.\n\n27. Additional Agreements: No supporting specifications found.\n\n28. Proof of Concept Participation: Precision AI Solutions confirms willingness to participate in a POC phase, proposes a 45-day timeframe, and offers the POC at no cost to the State.\n\n29. Pricing Model: The service is offered on a subscription basis with tiered pricing reflective of usage volume and functional modules selected.\n\n30. Implementation Costs: Costs for deployment, training, and support are bundled into a fixed schedule, with add-on services available at pre-defined hourly rates.\n\n31. Licensing Terms: Licensing is flexible and scalable to the needs and size of the State's procurement operations.\n\n32. Alternative Approaches: A phased transition strategy is recommended to allow end users to acclimate to the new tool while preserving ongoing procurement activities. Periodic performance reviews and iterative optimization are also suggested."""
    # rdp_response_document_1 = {
    #     "document_name": "rfi_response_1.pdf",
    #     "document_id": "4321",
    #     "content": {
    #         "pdf_md": "",
    #         "chunks": "",
    #         "summary": summary_2
    #     }
    # }
    # rdp_response_document_1["content"]["summary_list"] = rdp_response_document_1["content"]["summary"].split('\n\n')
    # st.session_state.rfp_response_documents.append(rdp_response_document_1)
    # st.session_state.rfp_response_documents.append(rdp_response_document_2)
    # # ---------------------
    # # This is for hardcoded testing only
    # # ---------------------

# ----------------------------------------
# Main Workflow to test ingetions pipeline. This will never be ran in the streamlit app.
# ----------------------------------------
# def main():
#     start_time = time.time()
      
#     chunk_size = 1600  # words per chunk.
#     overlap = 50       # words overlap.
#     compare_documents = True


    
#     # ---------------------
#     # Read the RFP document and convert to MD
#     # ---------------------
#     pdf_path = "backend/RFP documents/RFP_requirements/Request_for_Information-GenAI_Procurement_Tools_2-5-25.pdf"
#     pdf_in_md = pdf_to_md(pdf_path)
#     # print(pdf_in_md)


#     # this is just for testing without hitting document intelligance __________________________
#     # pdf_md_path = "RFP documents/RFP_requirements/rfi_md.txt"
#     # with open(pdf_md_path, "r", encoding="utf-8") as f:
#     #     pdf_in_md = f.read()
#     # this is just for testing ________________________________________________________________
   

#     # ---------------------
#     # Index MD Documents in AI Search
#     # ---------------------
#     doc_id = str(uuid.uuid4())
#     md_chuncks = chunk_on_md(pdf_in_md, doc_id)
#     document = {
#         "document_name": "rfi_md",
#         "document_id": doc_id,
#         "content": {
#             "pdf_md": pdf_in_md,
#             "chunks": md_chuncks
#         }
#     }
    
#     create_embeddings_for_document(document)
#     documents = [document]
#     upload_documents_to_aisearch(documents)
        


#     # ---------------------
#     # Extract RFP requirements.
#     # ---------------------
#     # for n in range(1):
#     rfp_chunks, rfp_dynamic_reqs = process_requirements(pdf_in_md, "RFP Document", chunk_size, overlap)

#     # Combine dynamic requirements from the RFP into global refined requirements.
#     combine_req_prompt_text = combine_requirements_prompt(rfp_dynamic_reqs)
#     global_refined_requirements = call_openai(combine_req_prompt_text, step_name="Combine Requirements from RFP Document")
#     logger.log_overall("Global refined summarization requirements generated from RFP document.")
   
#     # print("----- Global Final Refined Requirements -----")
#     # print(global_refined_requirements)
#     # print("\n")
   
#     # # ---------------------
#     # # Read documents to be summarized.
#     # # ---------------------
#     documents_dir = os.path.join("backend", "RFP documents")
#     document_files = [f for f in os.listdir(documents_dir) if f.endswith(".txt")]
#     docs_data = {}
#     for file in document_files:
#         file_path = os.path.join(documents_dir, file)
#         with open(file_path, "r", encoding="utf-8") as f:
#             docs_data[os.path.splitext(file)[0]] = f.read()
   
#     # Process each document sequentially (chunk-level parallelization is done inside).
#     final_summaries = {}
#     for doc_title, doc_text in docs_data.items():
#         final_summary = process_document_summarization(doc_title, doc_text, chunk_size, overlap, global_refined_requirements)
#         final_summaries[doc_title] = final_summary
   
#     # # ---------------------
#     # # Optional: Compare Document Summaries if more than one.
#     # # ---------------------
#     # if len(final_summaries) >= 2 and compare_documents:
#     #     compare_summaries(final_summaries, global_refined_requirements)
   
#     total_time = time.time() - start_time
#     logger.log_overall(f"\n# Run Metadata")
#     logger.log_overall(f"Total Processing Time: {total_time:.2f} seconds")
   
#     # total_tokens = count_tokens(logger.overall_log + "\n" + logger.detailed_log)
#     # logger.log_overall(f"Total Token Count (not including reasoning): {total_tokens}")


#     # # ---------------------
#     # # Optional: Print metrics for requirements generation
#     # # ---------------------
#     logger.log_overall(f"\n Total requirements: {total_reqs}")
#     if len(total_reqs) > 2:
#         sorted_numbers = sorted(total_reqs)
#         differences = [abs(sorted_numbers[i+1] - sorted_numbers[i]) for i in range(len(sorted_numbers)-1)]
#         total_reqs_dif = sum(differences) / len(differences)
#         logger.log_overall(f"\n Total requirements average difference : {total_reqs_dif}")

#     logger.log_overall(f"\n Total requirements distance range: {max(total_reqs) - min(total_reqs)}")


#     # Save the overall and detailed logs via the logger.
#     logger.save_log_file()

# if __name__ == "__main__":
#     main()

