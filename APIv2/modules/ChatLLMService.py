import typing as t

import sqlalchemy.orm as so

from google.oauth2.service_account import Credentials

from .Services.PermissionAndQuota.Quota import QuotaService
from .Services.PermissionAndQuota.Permission import PermissionService
from .Services.PermissionAndQuota.ServiceBase import (
    ServiceWithAAA,
    quotaRequired,
    permissionRequired,
)
from .Services.User.User import UserChatRecordService

from .ApplicationModel import User

from .Services.ServiceDefination import (
    ServiceActionDefination,
    CHATLLM_INVOKE as INVOKE,
    CHATLLM_RECALL as RECALL,
    CHATLLM_CREATE as CREATE,
)

from ChatLLMv2.ChatModel.Property import AdditionalModelProperty, InvokeContextValues
from ChatLLMv2.DataHandler import ChatMessage
from ChatLLMv2.ChatController import ChatController
from ChatLLMv2.ChatModel.v1ChainMigrate import v1LLMChainModel


class ChatLLMServiceError(Exception):
    """Base exception class for ChatLLMService errors."""
    pass


class ChatLLMService(ServiceWithAAA):
    def __init__(self,
                 user: User,
                 dbSession: so.Session,
                 quotaService: QuotaService,
                 permissionService: PermissionService,
                 userChatRecordService: UserChatRecordService,
                 credentials: t.Optional[Credentials],
                 llmModelProperty: AdditionalModelProperty,
                 ) -> None:
        super().__init__(dbSession, "ChatLlmService", quotaService, permissionService, user)
        self.user = user
        self.userChatRecordService = userChatRecordService
        self.llmModel = v1LLMChainModel(credentials, llmModelProperty)

    def checkUserChatIdAssociation(self, chatId: str) -> bool:
        """
        Check if the user is associated with the chatId.

        :return: True if the user is associated with the chatId, False otherwise.
        """
        self.loggerDebug(f"Checking if user {self.user.id} is associated with chatId {chatId}")
        record = self.userChatRecordService.getByChatId(chatId)
        if record is None:
            return False
        return record.user.id == self.user.id

    @permissionRequired(INVOKE)
    @quotaRequired(INVOKE)
    def invokeChatModel(self, chatId: str, message: ChatMessage, contextValues: InvokeContextValues,
                        bypassChatAssociationCheck: bool = False,
                        bypassPermssionCheck: bool = False,  # for decorator
                        bypassQuotaCheck: bool = False,  # for decorator
                        ) -> ChatMessage:
        """
        Invoke the chat service with a user and a message.

        :param message: The message to send in the chat.
        :param contextValues: Additional context values for the chat invocation.
        :param bypassPermssionCheck: Whether to bypass the permission check.
        :param bypassChatAssociationCheck: Whether to bypass the chat ID association check.
        :return: The response from the chat service.
        """
        if not self.checkUserChatIdAssociation(chatId) and not bypassChatAssociationCheck:
            raise PermissionError("The user is not associated with the specified chatId.")

        self.loggerInfo(f"Invoking chat model for user {self.user.id} with chatId {chatId}")
        try:
            return ChatController(
                dbSession=self.dbSession,
                llmModel=self.llmModel,
                chatId=chatId,
            ).invokeLLM(message, contextValues)
        except Exception as e:
            self.loggerError(f"Error invoking chat model for user {self.user.id} with chatId {chatId}: {e}")
            raise ChatLLMServiceError("Failed to invoke chat model.")

    @permissionRequired(CREATE)
    @quotaRequired(CREATE)
    def createChat(self, chatId: t.Optional[str] = None,
                   bypassPermissionCheck: bool = False,  # for decorator
                   bypassQuotaCheck: bool = False,  # for decorator
                   ) -> str:
        """
        Create a new chat session for the user and associate it with the user profile.

        :param chatId: The ID of the chat session to create.
        :param bypassPermissionCheck: Whether to bypass the permission check.
        :return: The ID of the created chat session.
        """
        self.loggerInfo(f"Creating chat session for user {self.user.id} with chatId: {chatId}")
        chatId = chatId if chatId else ChatController(
            dbSession=self.dbSession,
            llmModel=self.llmModel,
            chatId=None,
        ).chatId
        self.loggerInfo(f"Creating chat session with chatId: {chatId} for user {self.user.id}")
        self.userChatRecordService.associateChatIdWithUser(chatId, self.user)
        self.loggerInfo(f"Chat session with chatId: {chatId} created and associated with user {self.user.id}")

        return chatId

    def recall(self, chatId: str,
               bypassPermissionCheck: bool = False,
               bypassChatAssociationCheck: bool = False,
               ) -> t.List[ChatMessage]:
        """
        Recall the chat session and return the messages.

        :param bypassPermissionCheck: Whether to bypass the permission check.
        :return: A list of messages in the chat session.
        """
        actionId = ServiceActionDefination.getId(RECALL)
        if not self.checkPermission(actionId) and not bypassPermissionCheck:
            raise PermissionError("User does not have permission to recall the chat session.")
        if not self.checkUserChatIdAssociation(chatId) and not bypassChatAssociationCheck:
            raise PermissionError("The user is not associated with the specified chatId.")
        self.loggerInfo(f"Recalling chat session with chatId: {chatId} for user {self.user.id}")
        return ChatController(
            dbSession=self.dbSession,
            llmModel=self.llmModel,
            chatId=chatId,
        ).currentChatRecords.messages
