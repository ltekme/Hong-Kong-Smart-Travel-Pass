import uuid
import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)

from ChatLLMv2 import DataHandler
from .models import chatLLMDataModel, ChatRecallModel
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
    requestChatId = messageRequest.chatId or str(uuid.uuid4())
    requestMessageText = messageRequest.content.message
    requestAttachmentList = messageRequest.content.media
    requestDisableTTS = messageRequest.disableTTS

    logger.debug(f"starting chatLLM request {messageRequest=}")
    if x_SessionToken is None:
        raise HTTPException(
            status_code=400,
            detail="No Session Found"
        )
    sessionTokenUserProfile = UserService.getUserProfileFromSessionToken(
        sessionToken=x_SessionToken,
        dbSession=dbSession,
        bypassExpire=False
    )
    if sessionTokenUserProfile is None:
        raise HTTPException(
            status_code=400,
            detail="Session Expired or invalid"
        )

    logger.debug(f"Getting {requestChatId=} associated profile")
    chatIdProfileRecord = UserService.getUserProfileChatRecordFromChatId(
        chatId=requestChatId,
        dbSession=dbSession,
    )
    if chatIdProfileRecord is None:
        if dbSession.query(DataHandler.ChatRecord).where(
            DataHandler.ChatRecord.chatId == requestChatId
        ).first() is not None:
            raise HTTPException(
                status_code=403,
                detail="Converstation No Longer Valid"
            )
        chatIdProfileRecord = UserService.associateChatIdWithUserProfile(
            chatId=requestChatId,
            userProfile=sessionTokenUserProfile,
            dbSession=dbSession,
        )
    if sessionTokenUserProfile != chatIdProfileRecord.profile:
        raise HTTPException(
            status_code=403,
            detail="Invalid"
        )

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


@router.get("/{chatId}", response_model=ChatRecallModel.Response)
async def chatRecall(
    chatId: str,
    chatController: chatControllerDepend,
) -> ChatRecallModel.Response:
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
