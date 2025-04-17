import os

# ----------------------------------------
# Helper: Load a prompt file from backend/prompts/
# ----------------------------------------
def load_prompt_file(filename):
    filepath = os.path.join("backend", "prompts", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# ----------------------------------------
# Prompt functions using external templates.
# ----------------------------------------
def generate_requirements_prompt(chunk, previous_requirements=""):
    GENERATE_REQ_PROMPT_TEMPLATE = load_prompt_file("generate_requirements_prompt_2.txt")

    return GENERATE_REQ_PROMPT_TEMPLATE.format(
        chunk=chunk,
        previous_requirements=previous_requirements
    )

def combine_requirements_prompt(all_dynamic_requirements):
    COMBINE_REQ_PROMPT_TEMPLATE = load_prompt_file("combine_requirements_prompt.txt")

    combined_dynamic = "\n".join(all_dynamic_requirements)
    return COMBINE_REQ_PROMPT_TEMPLATE.format(
        combined_dynamic=combined_dynamic,
    )

def summarize_chunk_prompt(chunk, refined_requirements):
    SUMMARIZE_CHUNK_PROMPT_TEMPLATE = load_prompt_file("summarize_chunk_prompt.txt")

    return SUMMARIZE_CHUNK_PROMPT_TEMPLATE.format(
        chunk=chunk,
        refined_requirements=refined_requirements
    )

def combine_summaries_prompt(chunk_summaries, refined_requirements):
    COMBINE_SUMMARIES_PROMPT_TEMPLATE = load_prompt_file("combine_summaries_prompt.txt")

    combined_summaries = "\n\n".join(chunk_summaries)
    return COMBINE_SUMMARIES_PROMPT_TEMPLATE.format(
        combined_summaries=combined_summaries,
        refined_requirements=refined_requirements
    )

def compare_documents_prompt(summary_a, summary_b, refined_requirements):
    COMPARE_DOCS_PROMPT_TEMPLATE = load_prompt_file("compare_documents_prompt.txt")

    return COMPARE_DOCS_PROMPT_TEMPLATE.format(
        refined_requirements=refined_requirements,
        summary_a=summary_a,
        summary_b=summary_b
    )

def generate_rfp_summary_prompt(rfp_document_chunk):
    RFP_SUMMARY_PROMPT_TEMPLATE = load_prompt_file("rfp_summary_prompt.txt")

    return RFP_SUMMARY_PROMPT_TEMPLATE.format(
        rdp_document=rfp_document_chunk,
    )

def generate_question_answering_prompt(original_query_from_chat, context_text):
    QUESTION_ANSWERING_PROMPT_TEMPLATE = load_prompt_file("question_answering.txt")
    return QUESTION_ANSWERING_PROMPT_TEMPLATE.format(
        original_query_from_chat=original_query_from_chat,
        context_text=context_text
    )

# ----------------------------------------
# New function to generate the resume retooling prompt
# ----------------------------------------
def generate_resume_retool_prompt(resume_document, rfp_summary):
    RESUME_RETOOL_PROMPT_TEMPLATE = load_prompt_file("resume_retool_prompt.txt")

    return RESUME_RETOOL_PROMPT_TEMPLATE.format(
        resume_document=resume_document,
        rfp_summary=rfp_summary
    )
