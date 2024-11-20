import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ChatLLMv2 import (
    ChatModel,
    ChatController,
    TableBase,
)
from .APIv2.Config import (
    GCP_AI_SA_CREDENTIAL_PATH,
    CHATLLM_DB_URL,
)
from .APIv2.DataModel import (
    MessageRequest,
)

load_dotenv('.env')
credentialsPath = GCP_AI_SA_CREDENTIAL_PATH
credentials = Credentials.from_service_account_file(credentialsPath)  # type: ignore


app = FastAPI(root_path="/api/v2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm = ChatVertexAI(
    model="gemini-1.5-flash-002",
    temperature=1,
    max_tokens=8192,
    timeout=None,
    top_p=0.95,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id,  # type: ignore
    region="us-central1",
)
llmModel = ChatModel.PureLLMModel(llm=llm)
dbEngine = sa.create_engine(url=CHATLLM_DB_URL, echo=True)
dbSession = so.Session(bind=dbEngine)
TableBase.metadata.create_all(dbEngine, checkfirst=True)
chatController = ChatController(dbSession=dbSession, llmModel=llmModel)


@app.post("/chat")
async def root(messageRequest: MessageRequest):
    return messageRequest
