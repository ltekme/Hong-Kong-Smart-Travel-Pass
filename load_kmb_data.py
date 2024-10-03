from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from google.oauth2.service_account import Credentials
from langchain_text_splitters import RecursiveJsonSplitter
import json


kmb_loaded = json.load(open('./bus.json', encoding='utf-8-sig'))
kmb_loaded = kmb_loaded['features']

stops = [f"coordinates " for s in kmb_loaded]
print("Total number of bus stops: ", len(kmb_loaded))


splitter = RecursiveJsonSplitter()
splits = splitter.create_documents(kmb_loaded)
# print(splits[0:5])
print("Total number of splits: ", len(splits))


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


chunks = list(divide_chunks(splits, 1000))
print("Total number of chunks: ", len(chunks))


credentials = Credentials.from_service_account_file(
    "ive-fyp-436703-3a208c6d96a0.json")

vertexAIEmbeddings = VertexAIEmbeddings(
    credentials=credentials,
    project=credentials.project_id,
    model_name="text-multilingual-embedding-002",
)

vertex_store = Chroma(
    collection_name='KMB',
    embedding_function=vertexAIEmbeddings,
    persist_directory='./chroma_db',
)

for c, i in enumerate(chunks):
    print(vertex_store.add_documents(i))
    print(f"Added {c+1} chunks")
