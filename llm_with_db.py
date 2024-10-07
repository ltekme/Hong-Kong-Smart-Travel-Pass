from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_google_vertexai import (
    VertexAIEmbeddings,
    ChatVertexAI
)
from google.oauth2.service_account import Credentials

credentials = Credentials.from_service_account_file(
    "ive-fyp-436703-3a208c6d96a0.json")

vertexAIEmbeddings = VertexAIEmbeddings(
    credentials=credentials,
    project=credentials.project_id,
    model_name="text-multilingual-embedding-002",
)

vectorStore = Chroma(
    collection_name="KMB",
    persist_directory='./chroma_db',
    embedding_function=vertexAIEmbeddings
)

llm = ChatVertexAI(
    model="gemini-1.0-pro",
    temperature=0.9,
    max_tokens=1024,
    timeout=None,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id,
    task="text-generation",
    region="us-central1",
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


retriever = vectorStore.as_retriever(search_type="similarity", search_kwargs={
                                     "k": 12},  retrieve_source_documents=True)


prompt = PromptTemplate.from_template(
    template="You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. \nQuestion: {question}\nContext: {context}\nAnswer:",
    partial_variables={"context": "context", "question": "question"})

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

q = {
    "question": "What routes are avalable at the amoy gardens station?"
}

print('-'*100 + '\n')

if q.get("question"):
    resault = rag_chain.invoke(q.get("question"))
    print("Question: " + q.get("question"))
    print("Answer:" + resault)
    print('\n' + '-'*100)
    exit()

resault = rag_chain.invoke(input("Question: "))
print("Answer:" + resault)
print('\n' + '-'*100)
