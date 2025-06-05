import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)
from ChatLLMv2 import DataHandler
from ChatLLMv2.ChatModel.Property import InvokeContextValues

from .models import (
    chatLLMDataModel,
    ChatRecallModel,
    ChatIdResponse
)
from ...config import (
    settings,
    logger,
)
from ...dependence import (
    googleServicesDepend,
    dbSessionDepend,
    llmModel,
    userChatRecordServiceDepend,
    userSessionServiceDepend,
    chatControllerDepend,
)
from ...modules.Services.user import UserChatRecordService, UserSessionService

router = APIRouter(prefix="/chatLLM")


def checkSessionTokenChatIdAssociation(
    chatId: str,
    sessionToken: t.Optional[str],
    userChatRecordService: UserChatRecordService,
    userSessionService: UserSessionService,
) -> bool:
    """
    Check if the session token is associated with the chatId.

    :param chatId: The chatId.
    :param sessionToken: The session token.
    :param dbSession: The database session to use.

    :return: True if the session token is associated with the chatId.
    """
    if sessionToken is None or not sessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    sessionTokenSession = userSessionService.getSessionFromSessionToken(
        sessionToken=sessionToken,
        bypassExpire=False
    )
    if sessionTokenSession is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    logger.info(f"Getting {chatId=} associated profile")
    chatIdProfileRecord = userChatRecordService.getByChatId(chatId)
    if chatIdProfileRecord is None:
        raise HTTPException(
            status_code=403,
            detail="Converstation No Longer Valid"
        )
    logger.debug(f"Validating {chatIdProfileRecord.profile.id=} == {sessionTokenSession.profile.id=}")
    if chatIdProfileRecord.profile != sessionTokenSession.profile:
        raise HTTPException(
            status_code=403,
            detail="The requested chatId does not belong to your session"
        )
    return True


@router.post("", response_model=chatLLMDataModel.Response)
async def chatLLM(
    googleServices: googleServicesDepend,
    messageRequest: chatLLMDataModel.Request,
    dbSession: dbSessionDepend,
    userSessionServiceDepend: userSessionServiceDepend,
    userChatRecordServiceDepend: userChatRecordServiceDepend,
    chatControllerDepend: chatControllerDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> chatLLMDataModel.Response:
    """
    Invoke the language model with a user message and get the response.
    """
    requestChatId = messageRequest.chatId
    requestMessageText = messageRequest.content.message
    requestAttachmentList = messageRequest.content.media
    requestDisableTTS = messageRequest.disableTTS
    userSessionService = userSessionServiceDepend(dbSession)
    userChatRecordService = userChatRecordServiceDepend(dbSession)

    logger.info(f"Validating chatLLM request {messageRequest=}")
    checkSessionTokenChatIdAssociation(
        chatId=requestChatId,
        sessionToken=x_SessionToken,
        userSessionService=userSessionService,
        userChatRecordService=userChatRecordService,
    )

    logger.debug(f"Parcing {requestChatId=} chat message")
    try:
        attachments = list(map(
            lambda url: DataHandler.MessageAttachment(url, settings.applicationChatLLMMessageAttachmentPath),
            requestAttachmentList
        )) if requestAttachmentList is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = DataHandler.ChatMessage("user", requestMessageText, attachments)
    contextValues = InvokeContextValues(
        location=messageRequest.location if messageRequest.location else "unknown",
    )
    logger.debug(f"Invoking {requestChatId=} controller")
    chatController = chatControllerDepend(dbSession, llmModel, requestChatId)
    response = chatController.invokeLLM(message, contextValues=contextValues)

    if not requestDisableTTS:
        try:
            ttsAudio = googleServices.textToSpeech(response.text)
        except Exception as e:
            logger.error(f"cannot perform tts {e}")
            ttsAudio = ""
    else:
        ttsAudio = ""
    dbSession.commit()
    return chatLLMDataModel.Response(
        message=response.text,
        chatId=chatController.chatId,
        ttsAudio=ttsAudio,
    )


@router.get("/recall/{chatId}", response_model=ChatRecallModel.Response)
async def chatRecall(
    chatId: str,
    dbSession: dbSessionDepend,
    userSessionServiceDepend: userSessionServiceDepend,
    userChatRecordServiceDepend: userChatRecordServiceDepend,
    chatControllerDepend: chatControllerDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatRecallModel.Response:
    """
    Recall a chat session and return the session.
    """
    logger.info(f"Recalling {chatId=} controller")
    checkSessionTokenChatIdAssociation(
        chatId=chatId,
        sessionToken=x_SessionToken,
        userSessionService=userSessionServiceDepend(dbSession),
        userChatRecordService=userChatRecordServiceDepend(dbSession),
    )
    chatController = chatControllerDepend(dbSession, llmModel, chatId)
    messages = chatController.currentChatRecords.messages
    responseMessageList = [ChatRecallModel.ResponseMessage(
        role=i.role,
        message=i.text,
        dateTime=str(i.dateTime)
    ) for i in messages if i.role != "system"]
    logger.debug(f"Recalled {chatId=} messages")
    return ChatRecallModel.Response(
        chatId=chatId,
        messages=responseMessageList
    )


@router.get("/request", response_model=ChatIdResponse)
async def chatRequest(
    dbSession: dbSessionDepend,
    userSessionServiceDepend: userSessionServiceDepend,
    userChatRecordServiceDepend: userChatRecordServiceDepend,
    chatControllerDepend: chatControllerDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatIdResponse:
    """
    Create a new chat session and return the chat ID.
    """
    userSessionService = userSessionServiceDepend(dbSession)
    userChatRecordService = userChatRecordServiceDepend(dbSession)
    logger.info(f"Creating new chat session")
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    userSession = userSessionService.getSessionFromSessionToken(
        sessionToken=x_SessionToken,
        bypassExpire=False
    )
    if userSession is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    chatController = chatControllerDepend(dbSession, llmModel, None)
    chatId = chatController.chatId
    userChatRecordService.associateChatIdWithUserProfile(
        chatId=chatId,
        userProfile=userSession.profile,
    )
    logger.debug(f"Returning {chatId=} to {userSession.id=}")
    dbSession.commit()
    return ChatIdResponse(chatId=chatId)
