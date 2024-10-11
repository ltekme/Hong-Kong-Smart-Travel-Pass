import os
import asyncio
import json
from google.oauth2.service_account import Credentials
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_google_vertexai import (
    VertexAIEmbeddings,
    ChatVertexAI
)

from langchain_community.document_loaders import JSONLoader

credentials = Credentials.from_service_account_file(
    "ive-fyp-436703-3a208c6d96a0.json")

vertexAIEmbeddings = VertexAIEmbeddings(
    credentials=credentials,
    project=credentials.project_id,
    model_name="text-multilingual-embedding-002",
)


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


async def load_json_file(file_path):
    loop = asyncio.get_event_loop()
    file_contents = await loop.run_in_executor(None, open, file_path, 'r', -1, 'utf-8-sig')
    data = await loop.run_in_executor(None, json.load, file_contents)
    print(f"Loaded {file_path}")
    data = data['features']

    vertex_store = Chroma(
        collection_name=data[0]['properties']['companyCode'],
        embedding_function=vertexAIEmbeddings,
        persist_directory='./chroma_db',
    )

    chunks = await loop.run_in_executor(None, divide_chunks, data, 1000)
    print(f"Divided {file_path}")

    tasks = []
    for c, chunk in enumerate(chunks):
        chunk_str = [json.dumps(item) for item in chunk]
        task = loop.run_in_executor(None, vertex_store.add_texts, chunk_str, [
                                    {'source': os.path.basename(file_path).split('\\')[-1]}])
        tasks.append(task)
        print(f"Added chunk {c+1} on " + file_path)

    return tasks


async def main():
    file_tasks = []

    for file in os.listdir("data"):
        file_path = os.path.join("data", file)
        file_tasks.append(load_json_file(file_path))

    all_tasks = await asyncio.gather(*file_tasks)
    flat_tasks = [task for sublist in all_tasks for task in sublist]

    await asyncio.gather(*flat_tasks)

if __name__ == "__main__":
    asyncio.run(main())