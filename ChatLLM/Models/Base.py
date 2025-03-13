import datetime
import copy
import typing as t
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage
from ..ChatMessage import MessageContent, ChatMessage
from ..ChatRecord import ChatRecord


class LLMModelBase:
    # used for typing

    def __init__(self,
                 llm: BaseChatModel,
                 tools: list[BaseTool] = [],
                 # Not Used
                 overide_chat_content: list[dict[str, str]] = [],
                 overide_direct_output: bool = False,
                 ) -> None:
        self.llm = llm
        self.tools = tools
        self.overide_direct_output = overide_direct_output
        self.overide_chat_content = overide_chat_content

    def process_invoke_context(self, context: str) -> str:
        new_context = "Current local datetime: {}\n".format(
            datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        return new_context + context

    def invoke(
        self,
        messages: ChatRecord,
        context: str,
    ) -> ChatMessage:
        messages_copy: ChatRecord = copy.deepcopy(messages)

        last_user_message = messages_copy.last_message
        if not last_user_message:
            return ChatMessage("system", "Please provide a message")

        messages_copy.remove_last_message()
        system_message = ""
        if messages_copy.system_message is not None:
            system_message = messages_copy.system_message.content.text
            messages_copy.remove_system_message()

        system_message += "\n\n" + self.process_invoke_context(context)

        messages_list: list[t.Any] = [("system", system_message),
                                      MessagesPlaceholder('chat_history'),
                                      HumanMessage(content=[last_user_message.content.text]
                                      + [img.as_lcMessageDict for img in last_user_message.content.media])
                                      ]
        prompt = ChatPromptTemplate(messages_list)
        response = self.llm.invoke(prompt.invoke({  # type: ignore
            "chat_history": messages_copy.as_list_of_lcMessages,
        }))
        return ChatMessage('ai', MessageContent(str(response.content)))  # type: ignore
