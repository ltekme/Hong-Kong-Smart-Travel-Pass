from mock_chat_llm import *

message_content = MessageContent

message = Message(
    role="ai",
    content="You are a helpful assistant! Your name is Bob."
)

print(message.human_message_list)