import os
import typing as t

from fastapi import Depends
from google.oauth2.service_account import Credentials

from langchain_google_vertexai import ChatVertexAI

import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLM.Tools import ExternalIo

from ChatLLMv2.ChatModel import Graph
from ChatLLMv2.ChatModel.Property import AdditionalModelProperty
from ChatLLMv2 import (
    ChatController,
    DataHandler,
)

from .modules.GoogleServices import GoogleServices

from .config import (
    settings,
    logger,
)

ExternalIo.setLogger(logger)
ChatController.setLogger(logger)
DataHandler.setLogger(logger)
Graph.setLogger(logger)


if not os.path.exists(settings.gcpServiceAccountFilePath):
    logger.warning(f"Google Service Account File not found: {settings.gcpServiceAccountFilePath}, may lead to errors if client not set up correctly")
    credentials = None
else:
    credentials = Credentials.from_service_account_file(settings.gcpServiceAccountFilePath)  # type: ignore

llm = ChatVertexAI(
    model="gemini-1.5-flash-002",
    temperature=0.5,
    max_tokens=8192,
    top_p=0.5,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id if credentials is not None else None,  # type: ignore
)

if True:
    from ChatLLM.Tools import LLMTools

    llmModelProperty = AdditionalModelProperty(
        llmTools=LLMTools(
            credentials=credentials,
        ).all,
    )

llmModel = Graph.GraphModel(llm, llmModelProperty)

dbEngine = sa.create_engine(url=settings.applicationDatabaseURI, connect_args={'check_same_thread': False}, logging_name=logger.name)


def getSession():
    with so.Session(dbEngine) as session:
        yield session


def getGoogleService() -> t.Generator[GoogleServices, None, None]:
    yield GoogleServices(credentials=credentials, apiKey=settings.googleApiKey)


dbSessionDepend = t.Annotated[so.Session, Depends(getSession)]
googleServicesDepend = t.Annotated[GoogleServices, Depends(getGoogleService)]
