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
                "Access-Control-Allow-Origin": "*",
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
chatLLM = chat_llm.ChatLLM(
    credentials=credentials
)


@app.route("/", methods=[HTTPMethod.POST, HTTPMethod.GET, HTTPMethod.OPTIONS])
def chat_messages() -> JsonResponse:
    response = JsonResponse()

    if request.method == HTTPMethod.OPTIONS:
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '300'
        }
        response.response_content = ""
        response.status = HTTPStatus.ACCEPTED
        return response

    if request.method != HTTPMethod.POST:
        response.status = HTTPStatus.METHOD_NOT_ALLOWED
        response.response_content = {"message": "Method not allowed"}
        return response

    request_json: dict = request.json or {"no": "data"}
    chat_id = request_json.get('chat_id', str(uuid.uuid4()))
    message = request_json.get("message", "")
    images = request_json.get('images', [])

    if not message:
        response.status = HTTPStatus.BAD_REQUEST
        response.response_content = {"message": "No chat message provided"}
        return response

    # Expected images is a list of string containing src data url for image
    images = list(map(
        lambda img: chat_llm.MessageContentImage.from_uri(img),
        images
    ))
    print(images)

    chatLLM.chatId = chat_id
    ai_response = chatLLM.new_message(message=message, images=images)

    response.status = HTTPStatus.OK
    response.response_content = {
        "chatId": chat_id,
        "message": ai_response.content.text,
    }
    return response


if __name__ == "__main__":
    app.run(debug=True)
