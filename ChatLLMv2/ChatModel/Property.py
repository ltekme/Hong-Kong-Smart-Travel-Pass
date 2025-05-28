import datetime
import typing as t

from pydantic import Field
from pydantic.dataclasses import dataclass

from langchain_core.tools import BaseTool


@dataclass
class AzureChatAIProperty:
    deploymentName: t.Optional[str] = Field(
        default=None,
        description="The Azure OpenAI Deployment Name.",
    )
    version: t.Optional[str] = Field(
        default=None,
        description="The Azure OpenAI Deployment version.",
    )
    apiKey: t.Optional[str] = Field(
        default=None,
        description="The Azure OpenAI Deployment Api Key.",
    )
    apiUrl: t.Optional[str] = Field(
        default=None,
        description="The Azure OpenAI Deployment Url.",
    )


@dataclass
class AdditionalModelProperty:
    openAIProperty: t.Optional[AzureChatAIProperty] = None
    llmTools: list[BaseTool] = Field(
        default=list(),
        description="List of tools to be used by the LLM. This is used to provide additional functionality to the LLM.",
    )


@dataclass
class InvokeContextValues:
    username: str = Field(
        default="unknown",
        description="The username of the user. This is used to provide context to the LLM.",
    )
    location: str = Field(
        default="unknown",
        description="The location of the user. This is used to provide context to the LLM.",
    )
    utctime: str = Field(
        default=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="The current UTC time in ISO format. This is used to provide context to the LLM.",
    )
