from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import (
    VertexAIEmbeddings,
    ChatVertexAI
)
from google.oauth2.service_account import Credentials
from langchain_community.agent_toolkits.load_tools import load_tools 
from langchain.agents import initialize_agent, AgentType, AgentExecutor

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

template = ChatPromptTemplate([
    ("system", "You are a helpful AI bot. You should answer the user's questions based on the contextinformatino given"),
    ("placeholder", "{conversation}")
])


while True:
    print("-"*80 + "\n")
    user_input = input("Message: ")
    if user_input == "exit":
        break
    converstaion = [("human", user_input)]
    prompt = template.invoke({"conversation": converstaion})
    agent = (
        prompt
        | llm
        | StrOutputParser()
    )
    print(agent.invoke())