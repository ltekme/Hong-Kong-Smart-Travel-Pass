import uuid
import datetime
import typing as t
from fastapi import (
    APIRouter,
    HTTPException,
    Header
)

from ChatLLMv2 import DataHandler
from ChatLLMv2.ChatModel.Property import AdditionalModelProperty
from .models import chatLLMDataModel
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
    ApplicationModel,
    LlmHelper
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

    logger.debug(f"Getting {requestChatId=} associated profile")
    existingChatIdUserProfileRecord = ApplicationModel.UserProifileChatRecords.fromChatId(
        chatId=requestChatId,
        dbSession=dbSession,
    )
    logger.debug(f"Checking if {requestChatId=} exists on data handler")
    existingChat = dbSession.query(DataHandler.ChatRecord).where(DataHandler.ChatRecord.chatId == requestChatId).first()

    if x_SessionToken is not None:
        logger.debug(f"{x_SessionToken[:10]=} provided for {requestChatId=}, checking session")
        userProfile = ApplicationModel.UserProfileSession.get(
            sessionToken=x_SessionToken,
            currentTime=datetime.datetime.now(datetime.UTC),
            dbSession=dbSession,
        )
        if userProfile is None:
            logger.debug(f"{x_SessionToken=} expired, user not found")
            raise HTTPException(
                status_code=400,
                detail="Session Expired"
            )
        logger.debug(f"{userProfile.facebookId=} provided for {requestChatId=}, checking chat match")
        if existingChatIdUserProfileRecord is not None and existingChatIdUserProfileRecord.profile != userProfile:
            logger.debug(f"{userProfile.facebookId=} provided for {requestChatId=}, record mismatch")
            raise HTTPException(
                status_code=400,
                detail="Chat is already associated with a profile"
            )
        logger.debug(f"{userProfile.facebookId=} provided for {requestChatId=}, checking is chat public")
        if existingChat is not None and existingChatIdUserProfileRecord is None:
            raise HTTPException(
                status_code=400,
                detail="Chat is public locked"
            )
        try:
            logger.debug(f"Associating {requestChatId=} with {userProfile.facebookId=}")
            existingChatIdUserProfileRecord = ApplicationModel.UserProifileChatRecords.add(
                chatId=requestChatId,
                userProfile=userProfile,
                dbSession=dbSession,
            )
        except Exception as e:
            logger.error(f"Error assoicating {requestChatId=} with {userProfile.facebookId=}")
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="Error associating profile with chatId provided"
            )
    elif existingChatIdUserProfileRecord is not None:
        raise HTTPException(
            status_code=403,
            detail="Chat is user locked"
        )

    try:
        attachments = list(map(
            lambda url: DataHandler.MessageAttachment(url, settings.attachmentDataPath),
            requestAttachmentList
        )) if requestAttachmentList is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = DataHandler.ChatMessage("user", requestMessageText, attachments)

    chatController.chatId = requestChatId
    addirionalModelProperty = AdditionalModelProperty()
    response = chatController.invokeLLM(message, addirionalModelProperty)

    if not requestDisableTTS:
        try:
            ttsAudio = googleServices.textToSpeech(response.text)
        except Exception as e:
            logger.error(f"cannot perform tts {e}")
            ttsAudio = ""
    else:
        ttsAudio = ""

    if x_SessionToken is not None:
        logger.debug(f"Generating chat summory for {requestChatId=}")
        summory = LlmHelper.createChatSummory(
            messages=chatController.currentChatRecords.messages
        )
        if existingChatIdUserProfileRecord is not None:
            existingChatIdUserProfileRecord.editSummory(
                newSummory=summory,
                dbSession=dbSession
            )

    return chatLLMDataModel.Response(
        message=response.text,
        chatId=chatController.chatId,
        ttsAudio=ttsAudio,
    )
