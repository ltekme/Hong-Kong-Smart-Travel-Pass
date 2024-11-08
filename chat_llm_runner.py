from chat_llm import *
import os
from google.oauth2.service_account import Credentials
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage

import chat_llm as cllm
import chat_llm_graph as cllmGraph

if __name__ == "__main__":
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)

    llm = ChatVertexAI(
        model="gemini-1.5-pro-002",
        temperature=1,
        max_tokens=8192,
        timeout=None,
        top_p=0.95,
        max_retries=2,
        credentials=credentials,
        project=credentials.project_id,
        region="us-central1",
    )
    llmGraph = cllmGraph.LLMGraphModel(llm=llm)
    llmGraph.show("./data/graph.png")
    chatLLM = cllm.ChatLLM(llm_model=llmGraph)

    while True:
        try:
            user_input = input(': ')
            # clear input line
            print('\033[1A\033[K', end="")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            HumanMessage(user_input).pretty_print()
            message = cllm.Message('human', user_input)
            resault = chatLLM.new_message(message.content.text)
            resault.lcMessage.pretty_print()
        except KeyboardInterrupt:
            print("bye !")
            break
