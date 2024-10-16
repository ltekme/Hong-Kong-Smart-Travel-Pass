import json
import typing as t
import uuid
from http import HTTPStatus, HTTPMethod

from werkzeug.routing import Rule
from flask import Flask, Response, request


class JsonResponse(Response):
    def __init__(self, **kwargs):
        super().__init__(
            content_type=kwargs.get("content_type", "application/json"),
            status=kwargs.get("status", HTTPStatus.OK),
            response=kwargs.get("response", {"Message": "Hello, World!"}),
            **kwargs
        )

    @property
    def response_content(self) -> t.Any:
        return self.response

    @response_content.setter
    def response_content(self, value: dict | list) -> None:
        self.response = json.dumps(value)


app = Flask(__name__)


@app.route("/")
@app.route("/api")
@app.route("/api/")
def hello_world():
    return "Hello, World!"


app.url_map.add(Rule("/api/chat", endpoint="chat_messages"))


@app.endpoint("chat_messages")
def chat_messages() -> JsonResponse:
    response = JsonResponse()

    if request.method != HTTPMethod.POST:
        response.status = HTTPStatus.METHOD_NOT_ALLOWED
        response.response_content = {"message": "Method not allowed"}
        return response

    if not request.is_json or request.json is None or (request.json or {"null": "data"}).get("message"):
        response.status = HTTPStatus.BAD_REQUEST
        response.response_content = {"message": "No chat message provided"}
        return response

    chat_id = request.cookies.get('chat_id')
    if chat_id is None:
        response.set_cookie('chat_id', uuid.uuid4())

    response.status = HTTPStatus.OK
    response.response_content = {
        "message": "Success",
    }
    return response


if __name__ == "__main__":
    app.run(debug=True)
