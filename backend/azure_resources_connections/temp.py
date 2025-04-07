import uuid
from azure.core.credentials import AzureKeyCredential
from azure.ai.openai import OpenAIClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

# ================================
# Configuration
# ================================

# Azure OpenAI settings (using the Azure OpenAI library)
aoai_endpoint = "https://<your-azure-openai-resource>.openai.azure.com/"
aoai_key = "<your-azure-openai-key>"
# Deployment name for your embedding model, e.g. "text-embedding-ada-002"
aoai_deployment = "text-embedding-ada-002"

# Azure AI Search settings
search_endpoint = "https://<your-search-service>.search.windows.net"
admin_key = "<your-search-admin-key>"
index_name = "document-chunks-index"

# ================================
# Step 1: Assume your chunks already exist
# For example, the following list is produced by your Document Intelligence process.
# Each chunk is a dict with keys: "id", "header", and "content"
chunks = [
    {
        "id": "chunk1",
        "header": "Introduction",
        "content": "This section introduces the main ideas..."
    },
    {
        "id": "chunk2",
        "header": "Methodology",
        "content": "In this section, we describe the methods used..."
    },
    # ... add more chunks as needed
]

# ================================
# Step 2: Compute Embeddings Using Azure OpenAI Library
# ================================

# Instantiate the Azure OpenAI client using the Azure SDK
aoai_client = OpenAIClient(endpoint=aoai_endpoint, credential=AzureKeyCredential(aoai_key))

def get_embedding_azure(text, deployment=aoai_deployment):
    """
    Generate an embedding for the given text using Azure OpenAI.
    """
    # The get_embeddings method accepts a list of inputs.
    response = aoai_client.get_embeddings(deployment_id=deployment, input=[text])
    # Extract the embedding from the response
    return response.data[0].embedding

# Process each chunk and add an "embedding" field
documents = []
for chunk in chunks:
    embedding = get_embedding_azure(chunk["content"])
    doc = {
        "id": chunk["id"],
        "header": chunk["header"],
        "content": chunk["content"],
        "embedding": embedding
    }
    documents.append(doc)

# ================================
# Step 3: Create or Update the Azure AI Search Index
# ================================

credential = AzureKeyCredential(admin_key)
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

# Define the schema for the index:
# - "id": key field (string)
# - "header": searchable text field
# - "content": searchable text field
# - "embedding": a collection of single precision floats
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="header", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(
        name="embedding",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=False  # not used for full-text search directly
    )
]

index = SearchIndex(name=index_name, fields=fields)
# For simplicity, create the index (in production, consider checking if it exists)
result = index_client.create_index(index)
print(f"Index '{result.name}' created.")

# ================================
# Step 4: Upload Documents into the Index
# ================================

search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)
upload_result = search_client.upload_documents(documents=documents)
print(f"Uploaded {len(upload_result.results)} documents.")

# ================================
# Step 5: Querying the Index
# ================================

# Example 1: Keyword Search
print("\nKeyword Search Results:")
keyword_results = search_client.search(search_text="introduction")
for res in keyword_results:
    print(f"ID: {res['id']}, Header: {res['header']}")
    print(f"Snippet: {res['content'][:100]}...\n")

# Example 2: Vector Similarity Search
# Compute the embedding for the query using the Azure OpenAI client
query_text = "overview of the introduction"
query_embedding = get_embedding_azure(query_text)

# Create a vectorized query: note that the SDK accepts a VectorizedQuery object.
vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=3, fields="embedding")
print("\nVector Search Results:")
vector_results = search_client.search(search_text=None, vector_queries=[vector_query])
for res in vector_results:
    print(f"ID: {res['id']}, Header: {res['header']}, Score: {res['@search.score']:.4f}")
    print(f"Snippet: {res['content'][:100]}...\n")