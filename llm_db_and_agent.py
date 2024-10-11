from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import (
    VertexAIEmbeddings,
    ChatVertexAI
)
from google.oauth2.service_account import Credentials
from langchain.agents import load_tools, initialize_agent, AgentType

credentials = Credentials.from_service_account_file(
    "ive-fyp-436703-3a208c6d96a0.json")

vertex_ai_embeddings = VertexAIEmbeddings(
    credentials=credentials,
    project=credentials.project_id,
    model_name="text-multilingual-embedding-002",
)

vector_store = Chroma(
    collection_name="KMB",
    persist_directory='./chroma_db',
    embedding_function=vertex_ai_embeddings
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, but don't know current events, Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.",
        ),
        ("user", "Context: {Context}\nQuestion:{input}"),
    ]
)

llm = ChatVertexAI(
    model="gemini-1.0-pro-vision",
    temperature=0.9,
    max_tokens=2048,
    timeout=None,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id,
    task="text-generation",
    region="us-central1",
)

llm_with_tools = load_tools(["wikipedia"], llm=llm)

question_data = {
    "question": "What routes are available at the Amoy Gardens station?"}

documents = vector_store.similarity_search(question_data.get("question"), k=12)
documents_page_content = " ".join([doc.page_content for doc in documents])

agent = (
    {"context": documents_page_content, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if question_data.get("question"):
    print('-' * 100 + '\n')
    print("Question: " + question_data.get("question"))
    result = agent.invoke(question_data.get("question"))
    print(result)
    print('\n' + '-' * 100)
    exit()
