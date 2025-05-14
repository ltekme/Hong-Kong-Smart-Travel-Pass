import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)
import sqlalchemy.orm as so

from ChatLLMv2 import DataHandler
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
    chatControllerDepend,
    googleServicesDepend,
    dbSessionDepend,
)
from ...modules import (
    UserService
)

router = APIRouter(prefix="/chatLLM")


def checkSessionTokenChatIdAssociation(
    chatId: str,
    sessionToken: str,
    dbSession: so.Session
) -> bool:
    """
    Check if the session token is associated with the chatId.

    :param chatId: The chatId.
    :param sessionToken: The session token.
    :param dbSession: The database session to use.

    :return: True if the session token is associated with the chatId.
    """
    sessionTokenUserProfile = UserService.getUserProfileFromSessionToken(
        sessionToken=sessionToken,
        dbSession=dbSession,
        bypassExpire=False
    )
    if sessionTokenUserProfile is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    logger.info(f"Getting {chatId=} associated profile")
    chatIdProfileRecord = UserService.getUserProfileChatRecordFromChatId(
        chatId=chatId,
        dbSession=dbSession,
    )
    if chatIdProfileRecord is None:
        raise HTTPException(
            status_code=403,
            detail="Converstation No Longer Valid"
        )
    if chatIdProfileRecord.profile != sessionTokenUserProfile:
        raise HTTPException(
            status_code=403,
            detail="The requested chatId does not belong to your session"
        )
    return True


@router.post("", response_model=chatLLMDataModel.Response)
async def chatLLM(
    googleServices: googleServicesDepend,
    chatController: chatControllerDepend,
    messageRequest: chatLLMDataModel.Request,
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> chatLLMDataModel.Response:
    """
    Invoke the language model with a user message and get the response.
    """
    requestChatId = messageRequest.chatId
    requestMessageText = messageRequest.content.message
    requestAttachmentList = messageRequest.content.media
    requestDisableTTS = messageRequest.disableTTS

    logger.info(f"starting chatLLM request {messageRequest=}")
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )

    checkSessionTokenChatIdAssociation(
        chatId=requestChatId,
        sessionToken=x_SessionToken,
        dbSession=dbSession
    )

    logger.info(f"Invoking {requestChatId=} chat controller")
    try:
        attachments = list(map(
            lambda url: DataHandler.MessageAttachment(url, settings.applicationChatLLMMessageAttachmentPath),
            requestAttachmentList
        )) if requestAttachmentList is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = DataHandler.ChatMessage("user", requestMessageText, attachments)

    chatController.chatId = requestChatId
    response = chatController.invokeLLM(message)

    if not requestDisableTTS:
        try:
            ttsAudio = googleServices.textToSpeech(response.text)
        except Exception as e:
            logger.error(f"cannot perform tts {e}")
            ttsAudio = ""
    else:
        ttsAudio = ""

    return chatLLMDataModel.Response(
        message=response.text,
        chatId=chatController.chatId,
        ttsAudio=ttsAudio,
    )


@router.get("/recall/{chatId}", response_model=ChatRecallModel.Response)
async def chatRecall(
    chatId: str,
    chatController: chatControllerDepend,
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatRecallModel.Response:
    logger.info(f"Recalling {chatId=} chat controller")
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )

    checkSessionTokenChatIdAssociation(
        chatId=chatId,
        sessionToken=x_SessionToken,
        dbSession=dbSession
    )

    chatController.chatId = chatId
    messages = chatController.currentChatRecords.messages
    responseMessageList = [ChatRecallModel.ResponseMessage(
        role=i.role,
        message=i.text,
        dateTime=str(i.dateTime)
    ) for i in messages if i.role != "system"]
    return ChatRecallModel.Response(
        chatId=chatId,
        messages=responseMessageList
    )


@router.get("/request", response_model=ChatIdResponse)
async def chatRequest(
    chatController: chatControllerDepend,
    dbSession: dbSessionDepend,
    x_SessionToken: t.Annotated[str | None, Header()] = None,
) -> ChatIdResponse:
    """
    Create a new chat session and return the chat ID.
    """
    logger.info(f"Creating new chat session")
    if x_SessionToken is None or not x_SessionToken.strip():
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    userProfile = UserService.getUserProfileFromSessionToken(
        sessionToken=x_SessionToken,
        dbSession=dbSession,
        bypassExpire=False
    )
    if userProfile is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )
    chatId = chatController.chatId
    UserService.associateChatIdWithUserProfile(
        chatId=chatId,
        userProfile=userProfile,
        dbSession=dbSession
    )
    return ChatIdResponse(chatId=chatId)
