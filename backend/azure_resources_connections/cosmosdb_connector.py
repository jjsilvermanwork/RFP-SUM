import os
from dotenv import load_dotenv
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from azure.core.pipeline.transport import RequestsTransport

load_dotenv()


COSMOS_ACCOUNT_URI = os.getenv("COSMOS_ACCOUNT_URI")
COSMOS_ACCOUNT_KEY = os.getenv("COSMOS_ACCOUNT_KEY")


transport = RequestsTransport(connection_verify=False)

cosmos_db_client = CosmosClient(COSMOS_ACCOUNT_URI, COSMOS_ACCOUNT_KEY, transport=transport)

database = cosmos_db_client.get_database_client("test")
container = database.get_container_client("test")


# for i in range(1, 10):
#     container.upsert_item({
#             'id': 'item{0}'.format(i),
#             'productName': 'Widget',
#             'productModel': 'Model {0}'.format(i)
#         }
#     )
    