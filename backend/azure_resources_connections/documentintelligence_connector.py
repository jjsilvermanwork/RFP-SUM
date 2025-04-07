import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import  DocumentContentFormat
from langchain.text_splitter import MarkdownHeaderTextSplitter
import uuid


load_dotenv()

DOCUMENTINTELLIGENCE_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
DOCUMENTINTELLIGENCE_API_KEY = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")


document_intelligence_client = DocumentIntelligenceClient(endpoint=DOCUMENTINTELLIGENCE_ENDPOINT, credential=AzureKeyCredential(DOCUMENTINTELLIGENCE_API_KEY))


def pdf_to_md(pdf_directory, sub_directory, pdf_name):
    """ Convert PDF document to markdown version using Azure Document Intell """
    pdf_directory_path = os.path.join(pdf_directory, sub_directory, pdf_name)
    with open(pdf_directory_path, "rb") as pdf_file:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", pdf_file, output_content_format=DocumentContentFormat.MARKDOWN
        )
        result = poller.result()

    markdown_output = result.content
    return markdown_output

def chunk_on_md(md_text, doc_id):
    """ Chunks markdown text by headers for semantic chunking  """
    # # Initiate Azure AI Document Intelligence to load the document. You can either specify file_path or url_path to load the document.
    # loader = AzureAIDocumentIntelligenceLoader(file_path="<path to your file>", api_key = DOCUMENTINTELLIGENCE_API_KEY, api_endpoint = DOCUMENTINTELLIGENCE_ENDPOINT, api_model="prebuilt-layout")
    # docs = loader.load()

    # Split the document into chunks base on markdown headers.

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    splits = text_splitter.split_text(md_text)

   
    chunks = []
    for idx, chunck in enumerate(splits):
        temp_chunk = {
            "id": idx,
            "document_id": doc_id,
            "header": chunck.metadata.get("Header 1"),
            "content": (chunck.metadata.get("Header 1") if chunck.metadata.get("Header 1") else "") + " " + chunck.page_content
        }
        chunks.append(temp_chunk)

    return chunks





# pdf_path = "backend/RFP documents/RFP_requirements/Request_for_Information-GenAI_Procurement_Tools_2-5-25.pdf"
# pdf_in_md = pdf_to_md(pdf_path)
# chunk_on_md(pdf_in_md)




# FOR INITIAL TEASTING ONLY
# url = "https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/documentintelligence/azure-ai-documentintelligence/samples/sample_forms/forms/Invoice_1.pdf"
# poller = document_intelligence_client.begin_analyze_document(
#     "prebuilt-layout", AnalyzeDocumentRequest(url_source=url), output_content_format=DocumentContentFormat.MARKDOWN
# )

# result = poller.result()
# print(result)
