import os
import typing as t

from fastapi import Depends
from google.oauth2.service_account import Credentials

import sqlalchemy as sa
import sqlalchemy.orm as so

from ChatLLM.Tools import ExternalIo, LLMTools

from ChatLLMv2.ChatModel import v1ChainMigrate
from ChatLLMv2.ChatModel.Property import AdditionalModelProperty, AzureChatAIProperty
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
v1ChainMigrate.setLogger(logger)


if not os.path.exists(settings.gcpServiceAccountFilePath):
    logger.warning(f"Google Service Account File not found: {settings.gcpServiceAccountFilePath}, may lead to errors if client not set up correctly")
    credentials = None
else:
    credentials = Credentials.from_service_account_file(settings.gcpServiceAccountFilePath)  # type: ignore


llmModelProperty = AdditionalModelProperty(
    llmTools=LLMTools(
        credentials=credentials,
    ).all,
    openAIProperty=AzureChatAIProperty(
        deploymentName=settings.azureOpenAIAPIDeploymentName,
        version=settings.azureOpenAIAPIVersion,
        apiKey=settings.azureOpenAIAPIKey,
        apiUrl=settings.azureOpenAIAPIUrl,
    ),
)

llmModel = v1ChainMigrate.v1LLMChainModel(credentials, llmModelProperty)
connectArgs: dict[str, t.Any] = dict()
if not settings.applicationDatabaseURI.startswith("postgresql"):
    connectArgs["check_same_thread"] = False
dbEngine = sa.create_engine(url=settings.applicationDatabaseURI, connect_args=connectArgs, logging_name=logger.name)


def getSession():
    with so.Session(dbEngine) as session:
        yield session


def getGoogleService() -> t.Generator[GoogleServices, None, None]:
    yield GoogleServices(credentials=credentials, apiKey=settings.googleApiKey)


dbSessionDepend = t.Annotated[so.Session, Depends(getSession)]
googleServicesDepend = t.Annotated[GoogleServices, Depends(getGoogleService)]
