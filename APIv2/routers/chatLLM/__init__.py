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
    dbSessionDepend,
    getGoogleServiceDepend,
    getUserSessionServiceDepend,
    getChatLLMServiceDepend,
)

router = APIRouter(prefix="/chatLLM")


@router.post("", response_model=chatLLMDataModel.Response)
async def chatLLM(
    getGoogleService: getGoogleServiceDepend,
    messageRequest: chatLLMDataModel.Request,
    dbSession: dbSessionDepend,
    getUserSessionService: getUserSessionServiceDepend,
    getChatLLMService: getChatLLMServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> chatLLMDataModel.Response:
    """
    Invoke the language model with a user message and get the response.
    """
    requestChatId = messageRequest.chatId
    requestDisableTTS = messageRequest.disableTTS
    logger.info(f"Validating chatLLM request {messageRequest=}")
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    logger.debug(f"Parcing {requestChatId=} chat message")
    try:
        attachments = list(map(
            lambda url: DataHandler.MessageAttachment(url, settings.applicationChatLLMMessageAttachmentPath),
            messageRequest.content.media
        )) if messageRequest.content.media is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = DataHandler.ChatMessage("user", messageRequest.content.message, attachments)
    contextValues = InvokeContextValues(
        location=messageRequest.location if messageRequest.location else "unknown",
    )
    logger.debug(f"Invoking {requestChatId=} controller")
    chatLLMService = getChatLLMService(dbSession, session.user)
    response: DataHandler.ChatMessage = chatLLMService.invokeChatModel(requestChatId, message, contextValues)

    ttsAudio = ""
    if not requestDisableTTS:
        try:
            ttsAudio = getGoogleService(dbSession, session.user).textToSpeech(response.text)
        except Exception as e:
            logger.error(f"cannot perform tts {e}")
            ttsAudio = ""

    dbSession.commit()
    return chatLLMDataModel.Response(
        message=response.text,
        chatId=requestChatId,
        ttsAudio=ttsAudio,
    )


@router.get("/recall/{chatId}", response_model=ChatRecallModel.Response)
async def chatRecall(
    chatId: str,
    dbSession: dbSessionDepend,
    getUserSessionService: getUserSessionServiceDepend,
    getChatLLMService: getChatLLMServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatRecallModel.Response:
    """
    Recall a chat session and return the session.
    """
    logger.info(f"Recalling {chatId=} controller")
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    chatLLMService = getChatLLMService(dbSession, session.user)
    messages: t.List[DataHandler.ChatMessage] = chatLLMService.recall(chatId)
    responseMessageList = list(map(lambda i: ChatRecallModel.ResponseMessage(
        role=i.role,
        message=i.text,
        dateTime=str(i.dateTime)
    ), filter(lambda i: i.role != "system", messages)))
    logger.debug(f"Recalled {chatId=} messages")
    return ChatRecallModel.Response(
        chatId=chatId,
        messages=responseMessageList
    )


@router.get("/request", response_model=ChatIdResponse)
async def chatRequest(
    dbSession: dbSessionDepend,
    getUserSessionService: getUserSessionServiceDepend,
    getChatLLMService: getChatLLMServiceDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatIdResponse:
    """Create a new chat session and return the chat ID."""
    session = getUserSessionService(dbSession).validateSessionToken(x_SessionToken)
    logger.info(f"Creating new chat session for {session.user.id=} with {session.id=}")
    chatLLMService = getChatLLMService(dbSession, session.user)
    chatId: str = chatLLMService.createChat()
    logger.debug(f"Returning {chatId=} to {session.id=}")
    dbSession.commit()
    return ChatIdResponse(chatId=chatId)
