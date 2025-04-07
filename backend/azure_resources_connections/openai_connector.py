import os
from dotenv import load_dotenv

from openai import AzureOpenAI


load_dotenv()

# Configure Azure OpenAI
AZURE_OPENAI_ENDPOINT_o1_MINI = os.getenv("AZURE_OPENAI_ENDPOINT_o1_MINI")
AZURE_DEPLOYMENT_NAME_o1_MINI = os.getenv("AZURE_DEPLOYMENT_NAME_o1_MINI")
API_VERSION_o1_MINI = os.getenv("API_VERSION_o1_MINI")

AZURE_OPENAI_ENDPOINT_4o = os.getenv("AZURE_OPENAI_ENDPOINT_4o")
AZURE_DEPLOYMENT_NAME_4o = os.getenv("AZURE_DEPLOYMENT_NAME_4o")
API_VERSION_4o = os.getenv("API_VERSION_4o")


AZURE_OPENAI_ENDPOINT_EMBEDDING = os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING")
API_VERSION_EMBEDDING= os.getenv("API_VERSION_EMBEDDING")
AZURE_DEPLOYMENT_NAME_EMBEDDING = os.getenv("AZURE_DEPLOYMENT_NAME_EMBEDDING")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Testing to be used for RFP response requirements answering
openai_o1_mini_client = AzureOpenAI(
    # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
    api_version=API_VERSION_o1_MINI,
    # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint=AZURE_OPENAI_ENDPOINT_o1_MINI,
)

# Testing to be used to RFP requirements extracting
openai_4o_client = AzureOpenAI(
    # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
    api_version=API_VERSION_4o,
    # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint=AZURE_OPENAI_ENDPOINT_4o,
)


openai_embedding_client = AzureOpenAI(
        api_key = AZURE_OPENAI_API_KEY,  
        api_version = API_VERSION_EMBEDDING,
        azure_endpoint = AZURE_OPENAI_ENDPOINT_EMBEDDING 
        )



def create_embeddings_for_document(document):
    chunks = document["content"]["chunks"]
    for chunk in chunks:
        embedding= openai_embedding_client.embeddings.create(
            input = chunk["content"],
            model = AZURE_DEPLOYMENT_NAME_EMBEDDING
            )
        chunk["embedding"] = embedding.data[0].embedding