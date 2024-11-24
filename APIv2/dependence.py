import typing as t

from fastapi import Depends
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials

import sqlalchemy as sa
import sqlalchemy.orm as so

from APIv2.modules.GoogleServices import GoogleServices
from ChatLLMv2 import (
    ChatModel,
    ChatController,
)

from .config import settings

credentials = Credentials.from_service_account_file(settings.gcpServiceAccountPath)  # type: ignore
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
dbEngine = sa.create_engine(url=settings.dbUrl, echo=True, connect_args={'check_same_thread': False})


def getSession():
    with so.Session(dbEngine) as session:
        yield session


def getChatController(dbSession: so.Session = Depends(getSession)):
    yield ChatController(dbSession=dbSession, llmModel=llmModel)


def getGoogleService():
    yield GoogleServices(credentials=credentials, apiKey=settings.googleApiKey)


dbSessionDepend = t.Annotated[so.Session, Depends(getSession)]
chatControllerDepend = t.Annotated[ChatController, Depends(getChatController)]
googleServicesDepend = t.Annotated[GoogleServices, Depends(getGoogleService)]
