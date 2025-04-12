import typing as t

from fastapi import Depends
from langchain_openai import AzureChatOpenAI
from google.oauth2.service_account import Credentials

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic import SecretStr
from APIv2.modules.GoogleServices import GoogleServices

from ChatLLMv2.ChatModel import v1ChainMigrate, PureLLM
from ChatLLMv2.ChatModel.Property import AdditionalModelProperty
from ChatLLMv2 import (
    ChatController,
    DataHandler,
)

from ChatLLM.Tools import LLMTools
from .config import (
    settings,
    logger,
)

credentials = Credentials.from_service_account_file(settings.gcpServiceAccountPath)  # type: ignore
# llm = ChatVertexAI(
#     model="gemini-1.5-flash-002",
#     temperature=0.5,
#     max_tokens=8192,
#     timeout=None,
#     top_p=0.5,
#     max_retries=2,
#     credentials=credentials,
#     project=credentials.project_id,  # type: ignore
#     region="us-central1",
# )
llm = AzureChatOpenAI(
    model="gpt-4o",
    temperature=1,
    azure_deployment=settings.openAIAPIDply,
    api_version=settings.openAIAPIversion,
    # max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=SecretStr(settings.openAIAPIKey),
    azure_endpoint=settings.openAIAPIUrl,
)

# Graph.setLogger(logger)
DataHandler.setLogger(logger)
ChatController.setLogger(logger)
v1ChainMigrate.setLogger(logger)
PureLLM.setLogger(logger)
tools = LLMTools(
    credentials=credentials,
    verbose=True
)
llmModelProperty = AdditionalModelProperty()
llmModelProperty.llmTools = tools.all

# llmModel = Bridge.v1Bridge(llm=llm, additionalLLMProperty=llmModelProperty)
llmModel = v1ChainMigrate.v1LLMChainModel(llm=llm, additionalLLMProperty=llmModelProperty)
# llmModel = PureLLM.PureLLMModel(llm=llm, additionalLLMProperty=llmModelProperty)


dbEngine = sa.create_engine(url=settings.dbUrl, connect_args={'check_same_thread': False}, logging_name=logger.name)


def getSession():
    with so.Session(dbEngine) as session:
        yield session


def getChatController(
    dbSession: so.Session = Depends(getSession)
) -> t.Generator[ChatController.ChatController, None, None]:
    yield ChatController.ChatController(dbSession=dbSession, llmModel=llmModel)


def getGoogleService() -> t.Generator[GoogleServices, None, None]:
    yield GoogleServices(credentials=credentials, apiKey=settings.googleApiKey)


dbSessionDepend = t.Annotated[so.Session, Depends(getSession)]
chatControllerDepend = t.Annotated[ChatController.ChatController, Depends(getChatController)]
googleServicesDepend = t.Annotated[GoogleServices, Depends(getGoogleService)]
