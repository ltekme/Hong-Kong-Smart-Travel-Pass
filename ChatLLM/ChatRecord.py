import os
import json
import copy
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .ChatMessage import ChatMessage, MessageContent, MessageContentMedia


class ChatRecord:
    _chat_messages: list[ChatMessage] = []

    def __init__(self, system_message_string: str | None = None) -> None:
        if system_message_string:
            system_message_content = MessageContent(system_message_string)
            system_message = ChatMessage('system', system_message_content)
            self._chat_messages.append(system_message)

    @property
    def as_list(self) -> list[ChatMessage]:
        return self._chat_messages

    @property
    def as_list_of_lcMessages(self) -> list[HumanMessage | AIMessage | SystemMessage]:
        return [msg.lcMessage for msg in self._chat_messages]

    def append(self, message: ChatMessage) -> None:
        if not isinstance(message, ChatMessage):
            raise ValueError("message must be of type Message")
        if message.role not in ["ai", "human", "system"]:
            raise ValueError("message role must be either 'ai' or 'human' or 'system'")
        if self._chat_messages:
            last_role = self._chat_messages[-1].role
            if last_role == 'system' and message.role == 'system':
                self._chat_messages.append(message)
                return
            if last_role == message.role:
                raise ValueError("message must be of different role")
        self._chat_messages.append(message)

    def save_to_file(self, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w', encoding="utf-8-sig") as f:
            messages = [
                {"role": msg.role, "content": msg.message_list}
                for msg in self._chat_messages]
            json.dump(messages, f, indent=4, ensure_ascii=False)

    def get_from_file(self, file_path: str) -> list:
        system_message_copy = self.system_message
        try:
            with open(file_path, 'r', encoding="utf-8-sig") as f:
                data_in_file = json.load(f)

            messages = []
            for msg in data_in_file:
                message_content_text = None
                message_content_media = []

                for content in msg['content']:
                    if content['type'] == 'text':
                        message_content_text = content['text']
                    if content['type'] == 'image_url':
                        message_content_media.append(
                            MessageContentMedia.from_uri(content['image_url']['url']))
                    if content['type'] == 'media':
                        message_content_media.append(
                            MessageContentMedia(
                                content["data"],
                                content["mime_type"],
                            )
                        )

                messages.append(ChatMessage(
                    role=msg['role'],
                    content=MessageContent(
                        text=message_content_text if message_content_text else '',
                        media=message_content_media
                    ))
                )

            self._chat_messages = messages
            return self._chat_messages

        except FileNotFoundError:
            if system_message_copy is not None:
                self._chat_messages = [system_message_copy]
            return self._chat_messages

        except json.JSONDecodeError as e:
            if system_message_copy is not None:
                self._chat_messages = [system_message_copy]
            return self._chat_messages

    @property
    def system_message(self) -> ChatMessage | None:
        if self._chat_messages:
            if self._chat_messages[0].role != 'system':
                return None
            return self._chat_messages[0]
        return None

    @system_message.setter
    def system_message(self, value: str) -> None:
        if self._chat_messages:
            if self._chat_messages[0].role != 'system':
                self._chat_messages.insert(0, ChatMessage('system', value))
                return
            self._chat_messages[0].content = MessageContent(value)
        return None

    def remove_system_message(self) -> ChatMessage | None:
        if self._chat_messages:
            if self._chat_messages[0].role == 'system':
                return self._chat_messages.pop(0)
        return None

    @property
    def last_message(self) -> ChatMessage | None:
        if self._chat_messages:
            if self._chat_messages[-1].role != 'system':
                return self._chat_messages[-1]
        return None

    def remove_last_message(self) -> ChatMessage | None:
        if self._chat_messages:
            if self._chat_messages[-1].role != 'system':
                return self._chat_messages.pop(-1)
        return None

    def __deepcopy__(self, memo):
        new_record = ChatRecord()
        new_record._chat_messages = copy.deepcopy(self._chat_messages, memo)
        return new_record
