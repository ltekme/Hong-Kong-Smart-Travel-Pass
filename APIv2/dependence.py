import os
import typing as t

from fastapi import Depends
from google.oauth2.service_account import Credentials

import sqlalchemy as sa
import sqlalchemy.orm as so

# from ChatLLM.Tools import ExternalIo, LLMTools

from ChatLLMv2.ChatModel import v1ChainMigrate
from ChatLLMv2.ChatModel.Property import AdditionalModelProperty, AzureChatAIProperty
from ChatLLMv2 import (
    ChatController,
    DataHandler,
)

from .modules.ApplicationModel import User

from .modules.Services.User.User import (
    UserService,
    RoleService,
    UserRoleService,
    UserChatRecordService,
    UserSessionService
)
from .modules.GoogleServices import GoogleServices
from .modules.Services.Permission.Permission import PermissionService
from .modules.Services.Permission.RolePermission import RolePermissionService
from .modules.Services.ServiceAction.ServiceAction import ServiceActionService
from .modules.ChatLLMService import ChatLLMService

from .config import (
    settings,
    logger,
)

# ExternalIo.setLogger(logger)
ChatController.setLogger(logger)
DataHandler.setLogger(logger)
v1ChainMigrate.setLogger(logger)


if not os.path.exists(settings.gcpServiceAccountFilePath):
    logger.warning(f"Google Service Account File not found: {settings.gcpServiceAccountFilePath}, may lead to errors if client not set up correctly")
    credentials = None
else:
    credentials = Credentials.from_service_account_file(settings.gcpServiceAccountFilePath)  # type: ignore


llmModelProperty = AdditionalModelProperty(
    # llmTools=LLMTools(
    #     credentials=credentials,
    # ).all,
    openAIProperty=AzureChatAIProperty(
        deploymentName=settings.azureOpenAIAPIDeploymentName,
        version=settings.azureOpenAIAPIVersion,
        apiKey=settings.azureOpenAIAPIKey,
        apiUrl=settings.azureOpenAIAPIUrl,
    ),
)

connectArgs: dict[str, t.Any] = dict()
if not settings.applicationDatabaseURI.startswith("postgresql"):
    connectArgs["check_same_thread"] = False
dbEngine = sa.create_engine(url=settings.applicationDatabaseURI, connect_args=connectArgs, logging_name=logger.name)


def getSession():
    with so.Session(dbEngine) as session:
        yield session


getGoogleServicesType = t.Callable[[so.Session, t.Optional[User]], GoogleServices]
getChatLLMServiceType = t.Callable[[so.Session, User], ChatLLMService]

getUserServiceType = t.Callable[[so.Session], UserService]
getPermissionServiceType = t.Callable[[so.Session], PermissionService]
getUserSessionServiceType = t.Callable[[so.Session], UserSessionService]
getUserChatRecordServiceType = t.Callable[[so.Session], UserChatRecordService]


def getGoogleService() -> getGoogleServicesType:
    def func(dbSession: so.Session, user: t.Optional[User]) -> GoogleServices:
        return GoogleServices(
            dbSession=dbSession,
            serivceName="google",
            user=user,
            credentials=credentials,
            apiKey=settings.googleApiKey,
        )
    return func


def getUserService() -> getUserServiceType:
    def func(dbSession: so.Session) -> UserService:
        permissionService = PermissionService(dbSession)
        rolePermissionService = RolePermissionService(dbSession)
        serviceActionService = ServiceActionService(dbSession)
        roleService = RoleService(dbSession, permissionService, rolePermissionService, serviceActionService,)
        userRoleService = UserRoleService(dbSession)
        return UserService(dbSession, roleService, userRoleService)
    return func


def getUserChatRecordService() -> getUserChatRecordServiceType:
    return lambda dbSession: UserChatRecordService(dbSession)


def getUserSessionService() -> getUserSessionServiceType:
    return lambda dbSession: UserSessionService(dbSession)


def getPermissionService() -> getPermissionServiceType:
    return lambda dbSession: PermissionService(dbSession)


def getChatLLMService() -> getChatLLMServiceType:
    def func(dbSession: so.Session, user: User) -> ChatLLMService:
        return ChatLLMService(
            user=user,
            dbSession=dbSession,
            userChatRecordService=UserChatRecordService(dbSession),
            serviceActionService=ServiceActionService(dbSession),
            credentials=credentials,
            llmModelProperty=llmModelProperty,
        )
    return func


dbSessionDepend = t.Annotated[so.Session, Depends(getSession)]

getGoogleServiceDepend = t.Annotated[getGoogleServicesType, Depends(getGoogleService)]
getChatLLMServiceDepend = t.Annotated[getChatLLMServiceType, Depends(getChatLLMService)]

getUserServiceDepend = t.Annotated[getUserServiceType, Depends(getUserService)]
getPermissionServiceDepend = t.Annotated[getPermissionServiceType, Depends(getPermissionService)]
getUserSessionServiceDepend = t.Annotated[getUserSessionServiceType, Depends(getUserSessionService)]
getUserChatRecordServiceDepend = t.Annotated[getUserChatRecordServiceType, Depends(getUserChatRecordService)]
