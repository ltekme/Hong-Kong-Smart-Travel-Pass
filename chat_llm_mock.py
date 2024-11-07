from chat_llm import *
import os
import base64
from google.oauth2.service_account import Credentials
from langchain_google_vertexai import ChatVertexAI

if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)

    llm_model = LLMChainModel(
        llm=ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=1,
            max_tokens=8192,
            timeout=None,
            top_p=0.95,
            max_retries=2,
            credentials=credentials,
            project=credentials.project_id,
            region="us-central1",
        ),
        tools=LLMChainTools(credentials).all,
    )
    chatLLM = ChatLLM(llm_model)
    chatLLM.chatId = "mock"
    chatLLM.llm_model.overide_file_path = "./chat_data/mock_overide.json"

    while True:
        msg = input("Human: ")
        if msg == "EXIT":
            break
        if not msg:
            pass

        # process image
        response = None
        media_content = []
        if ':image' in msg:
            while True:
                image_path = input("Image Path: ")
                if image_path == "DONE":
                    break
                with open(image_path, 'rb') as f:
                    media_content.append(
                        MessageContentMedia(
                            format=image_path.split('.')[-1],
                            data=base64.b64encode(f.read()).decode('ASCII')))
            msg.replace(':image', '')

        response = chatLLM.new_message(msg, media_content)
        # print("ChatID: " + chatLLM.chatId)
        # print(response.lcMessage.pretty_print())
        print(f"AI({chatLLM.chatId}): " + response.content.text)
