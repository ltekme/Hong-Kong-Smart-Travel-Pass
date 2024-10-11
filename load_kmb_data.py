from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from google.oauth2.service_account import Credentials
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json


kmb_loaded = json.load(open('./b.json', encoding='utf-8-sig'))



print("Total number of bus stops: ", len(stops))


# splitter = RecursiveCharacterTextSplitter()
# splits = splitter.create_documents(stops)
# print(splits[0])
# print(splits[0:5])
print("Total number of splits: ", len(stops))

input('Press Enter to continue...')


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


chunks = list(divide_chunks(stops, 1000))
print("Total number of chunks to load: ", len(chunks))


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
    print(vertex_store.add_texts(i, metadatas=[{'source': 'KMB_STOPS_JSON'}]))
    print(f"Added {c+1} chunks")
