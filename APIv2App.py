import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ChatLLMv2 import (
    ChatManager,
    ChatModel,
    ChatController,
    TableBase,
    GoogleServices
)
from APIv2.Config import (
    GCP_AI_SA_CREDENTIAL_PATH,
    CHATLLM_DB_URL,
    CHATLLM_ATTACHMENT_URL,
)
from APIv2.DataModel import (
    chatLLMDataModel,
    geocodeDataModel,
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
googleServices = GoogleServices.GoogleServices(credentials)


@app.post("/chatLLM", response_model=chatLLMDataModel.Response)
async def chatLLM(messageRequest: chatLLMDataModel.Request) -> chatLLMDataModel.Response:
    """
    Invoke the language model with a user message and get the response.
    """
    requestChatId = messageRequest.chatId or str(uuid.uuid4())
    requestMessageText = messageRequest.content.message
    requestAttachmentList = messageRequest.content.media
    requestContextDict = messageRequest.context
    requestDisableTTS = messageRequest.disableTTS

    contexts = list(map(
        lambda co: ChatManager.MessageContext(co, requestContextDict[co]),
        requestContextDict.keys()
    )) if requestContextDict is not None else []

    try:
        attachments = list(map(
            lambda url: ChatManager.MessageAttachment(url, CHATLLM_ATTACHMENT_URL),
            requestAttachmentList
        )) if requestAttachmentList is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = ChatManager.ChatMessage("user", requestMessageText, attachments, contexts)

    chatController.chatId = requestChatId
    response = chatController.invokeLLM(message)

    if not requestDisableTTS:
        ttsAudio = googleServices.textToSpeech(response.text)
    else:
        ttsAudio = ""

    return chatLLMDataModel.Response(
        message=response.text,
        chatId=chatController.chatId,
        ttsAudio=ttsAudio,
    )


@app.post("/geocode", response_model=geocodeDataModel.Response)
def get_geocoding(location: geocodeDataModel.Request) -> geocodeDataModel.Response:
    """
    Get the location information for a given geocode.
    """

    return geocodeDataModel.Response(
        localtion="abcd"
    )
