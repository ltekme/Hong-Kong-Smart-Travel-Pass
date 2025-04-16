import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..DataHandler import ChatRecord, ChatMessage
from .Base import BaseModel

from .Property import AdditionalModelProperty

import typing as t
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_structured_chat_agent, AgentExecutor  # type: ignore
from google.api_core.exceptions import InvalidArgument


logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


class v1LLMChainModel(BaseModel):
    """Model class for pure language model interactions."""
    system_prompt_template = """Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond 
Action:
```
{{
  "action": "Final Answer",
  "action_input": "Final response to human"
}}

Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Format is Action:```$JSON_BLOB```then Observation"""


    def get_response_from_llm(self,
                              messagesRecord: ChatRecord,
                              ) -> t.Dict[str, t.Any]:
        messages: list[t.Any] = [
            ('system', self.system_prompt_template),
            ('user', f'''<context>
    <userLocation>{self.additionalLLMProperty.location}</userLocation>
</context>'''),
            MessagesPlaceholder('chat_history'),
            ("system",
             "{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what and response with markdown in the Final Answer response json blob.)")]
        prompt = ChatPromptTemplate(messages)
        executor = AgentExecutor(
            agent=create_structured_chat_agent(
                self.llm, self.tools, prompt),
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )
        return executor.invoke({
            "chat_history": messagesRecord.asLcMessages,
        })
    
    def __init__(self,
                 llm: BaseChatModel,
                 additionalLLMProperty: AdditionalModelProperty | None = None,
                 ) -> None:
        super().__init__(llm, additionalLLMProperty)
        logger.debug("Creating ChatLLMv1 Bridge")
        self.llm = llm
        if additionalLLMProperty is None:
            return
        self.additionalLLMProperty = additionalLLMProperty
        self.tools = additionalLLMProperty.llmTools


    def invoke(self, chatRecord: ChatRecord) -> ChatMessage:
        # last_user_message = chatRecord.messages.pop(-1)
        try:
            result = self.get_response_from_llm(
                # last_user_message,
                chatRecord,
            )
            return ChatMessage('ai', result['output'])
        except InvalidArgument as e:
            if not isinstance(e.message, str) or ("image" in e.message and "not valid" in e.message):
                return ChatMessage('ai',"An invalid image is provided")
            return ChatMessage('ai', "Something went wrong")


