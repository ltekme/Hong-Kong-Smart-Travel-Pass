import logging

from ..DataHandler import ChatRecord, ChatMessage
from .Base import BaseModel

from .Property import AdditionalModelProperty, InvokeContextValues

import typing as t

from pydantic import SecretStr

from google.oauth2.service_account import Credentials

from langchain_openai import AzureChatOpenAI
from langchain_google_vertexai import ChatVertexAI, HarmBlockThreshold, HarmCategory

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_structured_chat_agent, AgentExecutor  # type: ignore


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
    systemPromptTemplate = (
        "You are a travel assistant designed to support a tourist in their journy."
        "You have access to real-time date, including time, weather, and more."
        "Your primary task is to help the tourist plan their trip and provide assistance on their question."
        "Use markdown in the \"Final Answer\" if possible."
        "The tool you have will provide realtime data."
        "Use tools avalable to provide the most accurate infromation possible.\n"
        "You have access to the following tools:\n"
        "{tools}\n"
        "Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n"
        """Valid "action" values: "Final Answer" or {tool_names}"""
        "Provide only ONE action per $JSON_BLOB, as shown:"
        "```"
        "{{"
        '  "action": $TOOL_NAME,'
        '  "action_input": $INPUT'
        "}}"
        "```\n"
        "Follow this format:\n"
        "Question: input question to answer\n"
        "Thought: consider previous and subsequent steps\n"
        "Action:\n"
        "```$JSON_BLOB```"
        "Observation: action result\n"
        "... (repeat Thought/Action/Observation N times)\n"
        "Thought: I know what to respond\n"
        "Action:\n"
        "```"
        "{{"
        "  \"action\": \"Final Answer\","
        "  \"action_input\": \"Final response to human\""
        "}}"
        "```"
        "Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Format is Action:```$JSON_BLOB```then Observation"
    )

    def get_response_from_llm(self,
                              messagesRecord: ChatRecord,
                              contextValues: InvokeContextValues
                              ) -> t.Dict[str, t.Any]:
        messages: list[t.Any] = [
            ('system', self.systemPromptTemplate),
            ('system', (
                f"<context>"
                f"    <userLocation>{contextValues.location}</userLocation>"
                f"    <userUTCTime>{contextValues.utctime}</userUTCTime>"
                f"</context>"
            )),
            MessagesPlaceholder('chat_history'),
            ("system",
             "{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what and response with markdown in the Final Answer response json blob.)")]
        prompt = ChatPromptTemplate(messages)
        executor = AgentExecutor(
            agent=create_structured_chat_agent(self.llm, self.tools, prompt),
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )
        return executor.invoke({
            "chat_history": messagesRecord.asLcMessages,
        })

    def __init__(self,
                 gcpCredentials: t.Optional[Credentials] = None,
                 additionalLLMProperty: AdditionalModelProperty | None = None,
                 ) -> None:
        super().__init__(additionalLLMProperty)
        logger.debug("Creating ChatLLMv1 Chanin Model")

        if self.additionalLLMProperty.openAIProperty is None:
            raise ValueError("additionalLLMProperty or openAIProperty must be provided")

        openAIProperty = self.additionalLLMProperty.openAIProperty
        self.tools = self.additionalLLMProperty.llmTools
        try:
            self.llm = AzureChatOpenAI(
                model="gpt-4o",
                temperature=1,
                azure_deployment=openAIProperty.deploymentName,
                api_version=openAIProperty.version,
                timeout=None,
                max_retries=2,
                api_key=SecretStr(openAIProperty.apiKey or ""),
                azure_endpoint=openAIProperty.apiUrl,
            )
        except Exception as e:
            logger.warning(f"Failed to create AzureChatOpenAI instance: {e} Createing ChatVertexAI instance instead")
            try:
                self.llm = ChatVertexAI(
                    model="gemini-2.0-flash-001",
                    temperature=1,
                    max_retries=2,
                    credentials=gcpCredentials,
                    project=gcpCredentials.project_id if gcpCredentials else None,  # type: ignore
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.OFF,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.OFF,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.OFF,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.OFF,
                    },
                    response_mime_type="application/json",
                    # response_schema={"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "action_input": {"type": "STRING"}}, "required": ["action", "action_input"]},
                )
            except Exception as e:
                logger.error(f"Failed to create ChatVertexAI instance: {e}")
                raise ValueError("Failed to initialize LLM model, check your configuration") from e

    def invoke(self, chatRecord: ChatRecord, contextValues: t.Optional[InvokeContextValues] = None) -> ChatMessage:
        contextValues = contextValues or InvokeContextValues()
        result = self.get_response_from_llm(chatRecord, contextValues)
        return ChatMessage('ai', result['output'])
