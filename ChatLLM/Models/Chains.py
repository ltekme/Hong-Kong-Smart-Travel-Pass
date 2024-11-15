
import copy
import typing as t
import datetime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_structured_chat_agent, AgentExecutor  # type: ignore
from google.api_core.exceptions import InvalidArgument

from . import Base
from ..ChatRecord import ChatRecord
from ..ChatMessage import ChatMessage, MessageContent


class LLMChainModel(Base.LLMModelBase):
    system_prompt_template = """{existing_system_prompt}\n\nAdditional Contexts:{additional_context}\n\nYou have access to the following tools:\n\n{tools}\n\nAll content from tools are real-time data.\n\nUse a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation"""

    def __init__(self,
                 llm: BaseChatModel,
                 tools: list[BaseTool] = [],
                 overide_chat_content: list = [],
                 overide_direct_output: bool = False,
                 ) -> None:
        super().__init__(llm, tools, overide_chat_content, overide_direct_output)

    def get_response_from_llm(self,
                              last_user_message: ChatMessage,
                              messages_copy: ChatRecord,
                              full_context: str,
                              system_message: str,
                              standard_response: list[str] = [],
                              ) -> t.Dict[str, t.Any]:
        messages = [
            ("system", self.system_prompt_template),
            MessagesPlaceholder('chat_history'),
            HumanMessage(
                content=[f"Input: {last_user_message.content.text} "] +
                [img.as_lcMessageDict for img in last_user_message.content.media]),
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
            "existing_system_prompt": system_message,
            "chat_history": messages_copy.as_list_of_lcMessages,
            "additional_context": full_context,
            "standard_response": "\n".join(standard_response),
        })

    def invoke(self,
               messages: ChatRecord,
               context: str,
               ) -> ChatMessage:
        messages_copy: ChatRecord = copy.deepcopy(messages)

        system_message_content = None
        if messages_copy.system_message and messages_copy.system_message.content:
            system_message_content = messages_copy.system_message.content.text
            messages_copy.remove_system_message()

        last_user_message = messages_copy.last_message
        if not last_user_message:
            return ChatMessage('ai', "Please provide a message")
        if last_user_message.role != 'human':
            return ChatMessage('ai', "Please provide a human message")
        messages_copy.remove_last_message()

        # handle overide standard answer
        standard_response = ["Standard Response",
                             "You should follow the standard response below"]

        if self.overide_chat_content:
            for m in self.overide_chat_content:
                if m["question"] in last_user_message.content.text:
                    if self.overide_direct_output:
                        return ChatMessage('ai', MessageContent(m["response"]))
                    standard_response.append(m["response"])

        # only include the standard response if there are more than the headers
        if len(standard_response) > 2:
            standard_response.append("End of Standard Response")
            print(f"LLMChainModel.invoke => Using {standard_response=}")
        else:
            standard_response = []

        full_context = "Current local datetime: {}\n".format(
            datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        full_context += context

        result = {}
        try:
            result = self.get_response_from_llm(
                last_user_message,
                messages_copy,
                full_context,
                system_message_content if system_message_content is not None else "",
                standard_response,
            )
        except InvalidArgument as e:
            if "image" in e.message and "not valid" in e.message:
                result["output"] = "An invalid image is provided"
            else:
                result["output"] = "Something went wrong"

        return ChatMessage('ai', MessageContent(result['output']))
