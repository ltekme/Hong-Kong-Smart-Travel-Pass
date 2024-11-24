import uuid
import logging
from fastapi import APIRouter, HTTPException

from ChatLLMv2 import DataHandler
from .models import chatLLMDataModel
from ...config import settings
from ...dependence import (
    chatControllerDepend,
    googleServicesDepend,
)

router = APIRouter(prefix="/chatLLM")
logger = logging.getLogger(__name__)


@router.post("", response_model=chatLLMDataModel.Response)
async def chatLLM(
    googleServices: googleServicesDepend,
    chatController: chatControllerDepend,
    messageRequest: chatLLMDataModel.Request,
) -> chatLLMDataModel.Response:
    """
    Invoke the language model with a user message and get the response.
    """
    requestChatId = messageRequest.chatId or str(uuid.uuid4())
    requestMessageText = messageRequest.content.message
    requestAttachmentList = messageRequest.content.media
    requestContextDict = messageRequest.context
    requestDisableTTS = messageRequest.disableTTS

    contexts = list(map(
        lambda co: DataHandler.MessageContext(co, requestContextDict[co]),
        requestContextDict.keys()
    )) if requestContextDict is not None else []

    try:
        attachments = list(map(
            lambda url: DataHandler.MessageAttachment(url, settings.attachmentDataPath),
            requestAttachmentList
        )) if requestAttachmentList is not None else []
    except:
        raise HTTPException(status_code=400, detail="Invalid Image Provided")

    message = DataHandler.ChatMessage("user", requestMessageText, attachments, contexts)

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
