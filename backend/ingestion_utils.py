# backend/ingestion_utils.py

import os
import time
import concurrent.futures
from datetime import datetime
import uuid
from dotenv import load_dotenv
import tiktoken
import logging
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
    summarize_chunk_prompt,
    generate_resume_retool_prompt  # Import the new function
)
from backend.azure_resources_connections.documentintelligence_connector import chunk_on_md, pdf_to_md, document_intelligence_client
from backend.azure_resources_connections.openai_api import generate_resume_retool_prompt, call_openai

logger = logging.getLogger(__name__)

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
        if total_reqs:
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
        else:
            self.log_overall("No requirements were extracted.")

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

    response = openai_4o_client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME_4o,
        messages=[{"role": "user", "content": prompt}],
        temperature=.3,
        top_p=.3,
    )
    output = response.choices[0].message.content  # Access output as a field.
    newline_count = output.count('\n')
    total_reqs.append(newline_count)
    prompt_with_newlines = f"{output}\n\n[NEWLINE COUNT: {newline_count}]"

    if step_name:
        logger.log_detailed(step_name, prompt, output, prompt_with_newlines)
    return output

def chunk_document(document, chunk_size, overlap=50):
    words = document.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks

def process_requirements(pdf_in_md, doc_title, chunk_size, overlap):
    logger.log_overall(f"# Processing Requirements for {doc_title}")
    chunks = chunk_document(pdf_in_md, chunk_size, overlap)
    logger.log_overall(f"Document divided into {len(chunks)} chunks.")
    dynamic_req_outputs = []
    rfp_summary = ""
    previous_requirements_accumulated = ""
    for idx, chunk in enumerate(chunks):
        prompt = generate_requirements_prompt(chunk, previous_requirements_accumulated)
        step_name = f"{doc_title} - Requirements for Chunk {idx+1}"
        req_response = call_openai(prompt, step_name=step_name)
        dynamic_req_outputs.append(req_response)
        previous_requirements_accumulated += "\n" + req_response
        logger.log_overall(f"Chunk {idx+1} requirements generated.")

    rfp_summary_prompt = generate_rfp_summary_prompt(chunks[0])
    rfp_summary = call_openai(rfp_summary_prompt)
    return chunks, dynamic_req_outputs, rfp_summary

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
   
    combine_prompt = combine_summaries_prompt(chunk_summaries, refined_requirements)
    final_summary = call_openai(combine_prompt, step_name=f"{doc_title} - Combine Summaries")
    logger.log_overall(f"Final summary for {doc_title} generated.")
    return final_summary

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

def upload_pdf_extract_reqs(st):
    def update_progress_bar(percent_complete, progress_text):
        progress_bar.progress(percent_complete)
        progress_label.text = (f"{progress_text}%")

    start_time = time.time()
    progress_label = st.text("Gathering Requirements...")
    progress_bar = st.progress(0)
    
    if st.session_state.rfp_selection:
        st.session_state.SESSION_DIR = upload_pdf_files(st.session_state.rfp_selection, st.session_state.uploaded_response_files)
    else:
        print("Throw error")

    update_progress_bar(25, "Gathering Requirements...")
    pdf_in_md = pdf_to_md(st.session_state.SESSION_DIR, "RFP", st.session_state.rfp_selection.name)

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

    update_progress_bar(75, "Extracting RFP Requirements")

    chunk_size = 1600  # words per chunk.
    overlap = 50       # words overlap.

    rfp_chunks, rfp_dynamic_reqs, rfp_summary = process_requirements(pdf_in_md, "RFP Document", chunk_size, overlap)

    combine_req_prompt_text = combine_requirements_prompt(rfp_dynamic_reqs)
    st.session_state.rfp_document["extracted_requirements"] = call_openai(combine_req_prompt_text, step_name="Combine Requirements from RFP Document")
    st.session_state.rfp_document["content"]["summary"] = rfp_summary 
    logger.log_overall("Global refined summarization requirements generated from RFP document.")
    

    logger.save_requirements_log_file(start_time=start_time)

def process_rfp_responses(st):
    def update_progress_bar(percent_complete, progress_text):
        progress_bar.progress(percent_complete)
        progress_label.text = (f"{progress_text}%")

    start_time = time.time()
    progress_label = st.text("Summarizing documents...")
    progress_bar = st.progress(0)

    update_progress_bar(10, "Converting PDFs")
    responses_in_md = []
    for vendor in st.session_state.vendors_selected:
        response = {
            "file_name": vendor,
            "md_content": pdf_to_md(st.session_state.SESSION_DIR, "responses", vendor)
        }
        responses_in_md.append(response)

    update_progress_bar(25, "Processing")
    st.session_state.rfp_response_documents = []

    for response in responses_in_md:
        doc_id = str.uuid.uuid4()
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

    update_progress_bar(50, "Summarizing Vendor Responses")

    for response in st.session_state.rfp_response_documents:
        chunk_size = 1600  # words per chunk.
        overlap = 50  
        response["content"]["summary"] = process_document_summarization(response["document_name"], response["content"]["pdf_md"], chunk_size, overlap, st.session_state.rfp_document["extracted_requirements"])
        response["content"]["summary_list"] = response["content"]["summary"].split('\n\n')
    print("test")

    logger.save_summary_log_file(start_time=start_time)

# backend/ingestion_utils.py

def process_resume_retooling(resume_content, rfp_summary, session_dir):
    """
    Process resume retooling using the provided RFP summary.
    
    Parameters:
    - resume_content: The content of the resume to be retooled.
    - rfp_summary: Summary of the RFP document.
    - session_dir: The directory path where files are stored.
    """
    import os
    import logging
    from backend.azure_resources_connections.openai_api import generate_resume_retool_prompt, call_openai

    logger = logging.getLogger(__name__)

    logger.info("Starting resume retooling process.")

    # Path to the resume retooler prompt template
    template_path = '/workspaces/RFP-SUM/backend/prompts/resume_retool_prompt.txt'

    # Generate the resume retooling prompt.
    logger.info("Generating resume retooling prompt.")
    retool_prompt = generate_resume_retool_prompt(resume_content, rfp_summary, template_path)
    
    # Make an OpenAI API call to retool the resume.
    logger.info("Calling OpenAI API to retool the resume.")
    retooled_resume = call_openai(retool_prompt, step_name="Retool Resume")
    
    # Log the outcome.
    logger.info("Resume retooling completed.")
    
    return retooled_resume

