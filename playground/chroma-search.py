import os

from google.oauth2.service_account import Credentials
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

CURRENT_FILE_PATH = os.path.dirname(__file__)

DB_PATH = os.path.join(CURRENT_FILE_PATH, "./chroma_db")

# https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv
# Fetch from ../download.mjs
RAW_DATA_FILE_PATH = os.path.join(
    CURRENT_FILE_PATH, "../data/mtr_lines_and_stations.csv")

credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", '../gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

embeddings = VertexAIEmbeddings(
    credentials=credentials,
    project=credentials.project_id,
    model_name="text-multilingual-embedding-002",
)

if not os.path.exists(DB_PATH):
    # Proceed to load data
    data_file = open(RAW_DATA_FILE_PATH, 'r', encoding="utf-8")
    raw_data = data_file.read()
    # Replace " with none
    raw_data = raw_data.replace("\"", "")
    data_lines = str(raw_data).split("\n")

    # Read csv headers
    headers = str(data_lines[0]).split(",")
    stations = [line.split(",") for line in data_lines[1:]]
    # Format CSV to Text Document
    station_texts = []
    for station in stations:
        if len(station) < 2 or station[0] == "":
            continue
        station_text = ""
        for i in range(len(headers)):
            station_text += f"{headers[i]}: {station[i]}, "
        # print(station_text)
        station_texts.append(station_text)

    vector_store = Chroma(
        collection_name="mtr_lines_and_stations",
        embedding_function=embeddings,
        # Where to save data locally, remove if not necessary
        persist_directory=DB_PATH,
    )

    vector_store.add_documents(
        [Document(page_content=station_text) for station_text in station_texts])


vector_store = Chroma(
    collection_name="mtr_lines_and_stations",
    embedding_function=embeddings,
    # Where to save data locally, remove if not necessary
    persist_directory=DB_PATH,
)

results = vector_store.similarity_search(
    # wrong station name, but simular
    "Kowlon bay",
    k=2,
)

for res in results:
    print(f"* {res.page_content} [{res.metadata}]")