import os
import json
import typing as t
import uuid

from http import HTTPStatus, HTTPMethod

from flask import Flask, Response, request

from google.oauth2.service_account import Credentials

from langchain_google_vertexai import ChatVertexAI

import chat_llm


class JsonResponse(Response):
    def __init__(self, **kwargs):
        super().__init__(
            content_type=kwargs.get("content_type", "application/json"),
            status=kwargs.get("status", HTTPStatus.OK),
            response=kwargs.get("response", {"Message": "Hello, World!"}),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '300',
                "Content-Type": "application/json",
            },
            **kwargs,
        )

    @property
    def response_content(self) -> t.Any:
        return self.response

    @response_content.setter
    def response_content(self, value: dict | list) -> None:
        self.response = json.dumps(value)


app = Flask(__name__)


credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)
llm_model = chat_llm.LLMChainModel(
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
    tools=chat_llm.LLMChainTools(credentials).all,
)
chatLLM = chat_llm.ChatLLM(llm_model)


@app.route("/", methods=[HTTPMethod.POST, HTTPMethod.GET, HTTPMethod.OPTIONS])
def chat_messages() -> JsonResponse:
    response = JsonResponse()

    # Handle preflight option request
    if request.method == HTTPMethod.OPTIONS:
        response.response_content = {}
        response.status = HTTPStatus.OK
        return response

    # Early kick for Non post request
    if request.method != HTTPMethod.POST:
        response.status = HTTPStatus.METHOD_NOT_ALLOWED
        response.response_content = {"message": "Method not allowed"}
        return response

    Example_Request_Schema = {
        # Context will directly appeded to str and sent to system prompt
        "context": {
            "location": "lat, lon",
            "language": "en"
        },
        # message and media will be transformed
        "content": {
            "message": "user message",
            "media": ["data url", "data url", "data url"]
        },
        # chat id to use
        "chatId": "chat id",
        # weather to follow overide file, will also use file with {chatId}_overide.json
        "overideContent": False | True,
    }

    no_data = {"no": "data"}
    request_json: dict = request.json or no_data

    content: dict = request_json.get('content', no_data)
    context: dict = request_json.get('context', no_data)
    overide: bool = request_json.get('overideContent', False)
    chatId: str = request_json.get('chatId', str(uuid.uuid4()))
    print(f"{request_json=}")
    print(f"{overide=}")

    message = content.get("message", "")
    media = content.get('media', [])
    chatLLM.chatId = chatId

    # Handle overide
    if overide:
        try:
            print(f"Loading file: {chatId}_overide.json")
            with open(f"./chat_data/{chatId}_overide.json", "r", encoding="utf-8") as f:
                overide_data = json.load(f)
                chatLLM.llm_model.overide_chat_content = overide_data
            # chatLLM.store_chat_records = False
            print(f"Overide: {chatLLM.llm_model.overide_chat_content=}")
        except Exception as e:
            print(f"Failed Overide {e=}")

    # Handle empty message
    if not message:
        response.status = HTTPStatus.BAD_REQUEST
        response.response_content = {"message": "No chat message provided"}
        return response

    # process context
    client_context = "\n".join(list(map(
        lambda co: f"{co}: {context[co]}",
        context.keys()
    )))

    # Expected media is a list of string containing src data url for image
    # media = list(filter(
    #     lambda x: bool(x), list(map(
    #         lambda content:
    #             chat_llm.MessageContentMedia.from_uri(
    #                 content) if content else None,
    #         media
    #     ))))

    messageMedia = []
    for mediaContent in media:
        mediaObj = chat_llm.MessageContentMedia.from_uri(
            mediaContent)
        if mediaObj is not None:
            messageMedia.append(mediaObj)

    # Send to llm
    ai_response = chatLLM.new_message(
        message=message, media=messageMedia, context=client_context)

    # return response from llm
    response.status = HTTPStatus.OK
    response.response_content = {
        "chatId": chatLLM.chatId,
        "message": ai_response.content.text,
    }
    return response


if __name__ == "__main__":

    app.run(debug=True)
