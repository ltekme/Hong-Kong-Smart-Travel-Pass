import os
import json
import typing as t
import uuid
from http import HTTPStatus, HTTPMethod

from flask import Flask, Response, request

from google.oauth2.service_account import Credentials

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
chatLLM = chat_llm.ChatLLM(credentials=credentials)


@app.route("/", methods=[HTTPMethod.POST, HTTPMethod.GET, HTTPMethod.OPTIONS])
def chat_messages() -> JsonResponse:
    response = JsonResponse()

    # Handle preflight option request
    if request.method == HTTPMethod.OPTIONS:
        response.response_content = ""
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
        # message and images will be transformed
        "content": {
            "message": "user message",
            "images": ["data url", "data url", "data url"]
        }
    }

    no_data = {"no": "data"}
    request_json: dict = request.json or no_data

    content: dict = request_json.get('content', no_data)
    context: dict = request_json.get('context', no_data)

    message = content.get("message", "")
    images = content.get('images', [])

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

    # Expected images is a list of string containing src data url for image
    images = list(map(
        lambda img: chat_llm.MessageContentMedia.from_uri(img),
        images
    ))

    # Send to llm
    chatLLM.chatId = request_json.get('chatId', str(uuid.uuid4()))
    ai_response = chatLLM.new_message(
        message=message, images=images, context=client_context)

    # return response from llm
    response.status = HTTPStatus.OK
    response.response_content = {
        "chatId": chatLLM.chatId,
        "message": ai_response.content.text,
    }
    return response


if __name__ == "__main__":
    app.run(debug=True)
