from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from google.oauth2.service_account import Credentials
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json


kmb_loaded = json.load(open('./bus.json', encoding='utf-8-sig'))

kmb_loaded = kmb_loaded['features']

stops = [f"""KMB Bus Stop Info
Coordinates: {s['geometry']['coordinates']}
RouteId: {s['properties']['routeId']}
Company: {s['properties']['companyCode']}
Route Name: {s['properties']['routeNameE']}
Route Type: {s['properties']['routeNameE']}
District: {s['properties']['district']},
Service Mode: {s['properties']['serviceMode']}
Special Type: {s['properties']['specialType']}
Journey Time: {s['properties']['journeyTime']}
Route Start Location(English): {s['properties']['locStartNameE']}
Route Start Location(Chinese): {s['properties']['locStartNameC']}
Route Start Location(Simplified Chinese): {s['properties']['locStartNameS']}
Route End Location(English): {s['properties']['locEndNameE']}
Route End Location(Chinese): {s['properties']['locEndNameC']}
Route End Location(Simplified Chinese): {s['properties']['locEndNameS']}
Route Hyperlink(Chinese): {s['properties']['hyperlinkC']}
Route Hyperlink(Simplified Chinese): {s['properties']['hyperlinkS']}
Route Hyperlink(English): {s['properties']['hyperlinkE']}
Full Fare: {s['properties']['fullFare']}
Last Update Date: {s['properties']['lastUpdateDate']}
Route Sequence: {s['properties']['routeSeq']}
Stop Sequence: {s['properties']['stopSeq']}
Stop ID: {s['properties']['stopId']}
Stop Pick Drop: {s['properties']['stopPickDrop']}
Stop Name(English): {s['properties']['stopNameE']}
Stop Name(Chinese): {s['properties']['stopNameC']}
Stop Name(Simplified Chinese): {s['properties']['stopNameS']}""" for s in kmb_loaded]
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
