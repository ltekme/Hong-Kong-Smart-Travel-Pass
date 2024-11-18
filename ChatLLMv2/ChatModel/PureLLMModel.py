import logging
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


from ..ChatManager import ChatRecord, ChatMessage
from . import BaseModel

logger = logging.getLogger(__name__)


class PureLLMModel(BaseModel):
    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        logger.debug(f"Invoking llm")
        prompt = ChatPromptTemplate(messages=[
            SystemMessage(str(chatRecord.systemMessage)),
            MessagesPlaceholder('chat_history'),
        ])
        prompt_value = prompt.invoke({"chat_history": chatRecord.asLcMessages})  # type: ignore
        response = self.llm.invoke(prompt_value)  # type: ignore
        return ChatMessage("ai", str(response.content))  # type: ignore
