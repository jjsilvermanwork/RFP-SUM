import os
import uuid
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from azure.search.documents.models import VectorizedQuery
from backend.azure_resources_connections.openai_connector import openai_embedding_client, openai_4o_client, AZURE_DEPLOYMENT_NAME_4o
from backend.prompts.prompt_configs import load_prompt_file, generate_question_answering_prompt

import streamlit as st

load_dotenv()

AZURE_SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

AZURE_DEPLOYMENT_NAME_EMBEDDING = os.getenv("AZURE_DEPLOYMENT_NAME_EMBEDDING")


aisearch_client = SearchClient(AZURE_SEARCH_SERVICE_ENDPOINT, AZURE_SEARCH_INDEX_NAME, AzureKeyCredential(AZURE_SEARCH_API_KEY))


def upload_documents_to_aisearch(documents):
    """ Takes documents that have already been chucked using chunk_on_md() and uploaded them to AI Search """
    documents_to_upload = []
    for doc in documents:
        for chunk in doc["content"]["chunks"]:
            document = {
                "id": str(uuid.uuid4()),
                "document_id": doc["document_id"],
                "header": chunk["header"],
                "content": chunk["content"],
                "document_name": doc["document_name"],
                "vector": chunk["embedding"]
            }
            documents_to_upload.append(document)
    # ![](Link to pdf that opens in a popup) p. 2
    result = aisearch_client.upload_documents(documents_to_upload)
    print("Upload of new document succeeded: {}".format(result[0].succeeded))

def ai_search_vector_query(query):
    embedding= openai_embedding_client.embeddings.create(
        input = query,
        model = AZURE_DEPLOYMENT_NAME_EMBEDDING
    ).data[0].embedding
    vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=5, fields="vector")

    # st.session_state.rfp_response_documents
    rfp_name = [st.session_state.rfp_document['document_name']]
    doc_lists = [response["document_name"] for response in st.session_state.rfp_response_documents]
    docs_list = rfp_name + doc_lists
    str_doc_list = '|'.join(docs_list)

    results = aisearch_client.search(  
        search_text=None,
        filter=f"search.in(document_name, '{str_doc_list}', '|')", 
        vector_queries=[vector_query],
    )  
    # for result in results:
    #     print(result)
    return results

# # Test searching on query vector
# temp = ai_search_vector_query("effort and minimizing potential risks")
# print(temp)


# # PULL FROM prompt_configs
# def put_together_rag_prompt(results):
#     chunk_number = 0
#     prompt_pieces = []
#     for result in results: #temp:
#         chunk_number += 1 
#         prompt_pieces.append(f"Here is context from chunk #{chunk_number}: {result['document_name']} Here is the content: {result["content"]}")
#     refined_requirements = load_prompt_file("static_requirements.txt")
#     final_prompt = combine_summaries_prompt(prompt_pieces, refined_requirements)
#     return final_prompt

def put_together_rag_prompt_revised(results):
    chunk_number = 0
    prompt_pieces = []
    for result in results: #temp:
        chunk_number += 1 
        prompt_pieces.append(f"Here is context from chunk #{chunk_number}: {result['document_name']} Here is the content: {result['content']}")
    context_text = '/n/n'.join(prompt_pieces)
    return context_text 


def send_prompt(final_prompt, chat_history):
    # response = openai_4o_client.completions.create(
    #     engine=AZURE_DEPLOYMENT_NAME_4o,
    #     prompt=final_prompt,
    #     max_tokens=2000
    # )
    response = openai_4o_client.chat.completions.create(
        messages=chat_history + ([
            # {
            #     "role": "system",
            #     "content": "You are a helpful assistant.",
            # },
            {
                "role": "user",
                "content": final_prompt,
            }
        ]),
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=AZURE_DEPLOYMENT_NAME_4o
    )

    return response.choices[0].message.content


def rag_pipeline(original_query_from_chat, chat_history):
    results = ai_search_vector_query(original_query_from_chat)
    # final_prompt = put_together_rag_prompt(results)
    context_text = put_together_rag_prompt_revised(results)
    final_prompt = generate_question_answering_prompt(original_query_from_chat, context_text)
    response = send_prompt(final_prompt, chat_history)
    return response

