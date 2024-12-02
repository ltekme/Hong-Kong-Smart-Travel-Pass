# this is examed from unitest as this will be depracted
import os
import time
import uuid
import json
import base64
import logging
import uvicorn
import typing as t
from dotenv import load_dotenv

from APIv2 import app
from fastapi.middleware.wsgi import WSGIMiddleware

from flask import Flask, request, Response, Blueprint
from http import HTTPStatus, HTTPMethod
from langchain_google_vertexai import ChatVertexAI
from google.oauth2.service_account import Credentials
from ChatLLM.gcpServices import GoogleServices
from ChatLLM import ChatManager, MessageContentMedia, LLMChainModel, LLMModelBase
# from ChatLLM import LLMTools
from ChatLLM.UserProfile import UserProfile


load_dotenv('.env')


credentialsFiles = list(filter(lambda f: f.startswith(
    'gcp_cred') and f.endswith('.json'), os.listdir('.')))
credentials = Credentials.from_service_account_file(
    credentialsFiles[0])
googleService = GoogleServices(
    credentials,
    maps_api_key=os.getenv('GOOGLE_API_KEY')
)

flaskbp = Blueprint('apiv1', __name__)
# llm_model = LLMChainModel(
# audio input only work on base model
llm_model = LLMModelBase(
    llm=ChatVertexAI(
        model="gemini-1.5-flash-002",
        temperature=1,
        max_tokens=8192,
        timeout=None,
        top_p=0.95,
        max_retries=2,
        credentials=credentials,
        project=credentials.project_id,
        region="us-central1",
    ),
    # tools=LLMTools(credentials, verbose=True).all,
)
chatLLM = ChatManager(llm_model)


class JsonResponse(Response):
    def __init__(self, **kwargs):
        super().__init__(
            content_type=kwargs.get("content_type", "application/json"),
            status=kwargs.get("status", HTTPStatus.OK),
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
        return self.data

    @response_content.setter
    def response_content(self, value: str) -> None:
        self.data = value


@flaskbp.route('/get_session', methods=[HTTPMethod.POST, HTTPMethod.OPTIONS])
def get_session():
    response = JsonResponse()

    if request.method == HTTPMethod.OPTIONS:
        response.response_content = json.dumps({})
        response.status = HTTPStatus.OK
        return response

    no_data = {"no": "data"}
    request_json: dict = request.json or no_data
    facebook_access_token: str = request_json.get('accessToken', "")

    if not facebook_access_token:
        response.response_content = json.dumps({"error": "No access token"})
        response.status_code = 400
        return response

    facebook_profile = UserProfile.from_facebook_access_token(facebook_access_token)
    if not facebook_profile.id:
        response.response_content = json.dumps({"error": "Invalid access token"})
        response.status_code = 400
        return response

    facebook_profile.get_summory()

    current_unix_time = int(time.time())
    session_timeout_seconds = 600
    session_expire_unix_time = current_unix_time + session_timeout_seconds
    random_session_id = str(uuid.uuid4())

    session_object = {
        "expire": session_expire_unix_time,
        "sessionId": random_session_id,
    }

    if not os.path.exists("./session_data"):
        os.makedirs("./session_data")

    with open(f"./session_data/{facebook_profile.id}.json", "w") as f:
        session_object_copy = session_object
        session_object_copy["accessToken"] = facebook_access_token
        f.write(json.dumps(session_object_copy, indent=4))

    response.response_content = json.dumps(session_object)
    return response


@flaskbp.route('/stt', methods=[HTTPMethod.POST, HTTPMethod.OPTIONS])
def get_sst():
    response = JsonResponse()

    if request.method == HTTPMethod.OPTIONS:
        response.response_content = json.dumps({})
        response.status = HTTPStatus.OK
        return response

    imageData = request.json.get('audioData') if request.json else ""
    base64ImageData0 = imageData.split(',')[1]
    base64ImageData1 = base64.b64decode(base64ImageData0)
    text = googleService.speakToText(base64ImageData1)
    response.response_content = json.dumps({"message": text})
    return response


@flaskbp.route('/chatLLM', methods=[HTTPMethod.POST, HTTPMethod.OPTIONS])
def get_information():
    response = JsonResponse()

    if request.method == HTTPMethod.OPTIONS:
        response.response_content = json.dumps({})
        response.status = HTTPStatus.OK
        return response

    no_data = {"no": "data"}
    request_json: dict = request.json or no_data
    content: dict = request_json.get('content', no_data)
    context: dict = request_json.get('context', no_data)
    message = content.get("message", "")
    media = content.get('media', [])

    # process context
    client_context = ""
    for co in context.keys():
        client_context += f"{co}: {context[co]}"

    # Expected images is a list of string containing src data url for image
    messageMedia = list(map(
        lambda img: MessageContentMedia.from_uri(img),
        media
    ))

    # Send to llm
    chatLLM.chatId = request_json.get('chatId', str(uuid.uuid4()))
    ai_response = chatLLM.new_message(
        message=message, media=messageMedia, context=client_context)  # type: ignore

    audio = googleService.speak(ai_response.content.text)
    # print("audio: " + audio)
    response.response_content = json.dumps({
        "message": ai_response.content.text,
        "ttsAudio": audio,
        "chatId": chatLLM.chatId,
    })
    return response


@flaskbp.route('/geocode', methods=[HTTPMethod.POST, HTTPMethod.OPTIONS])
def get_geocoding():
    response = JsonResponse()

    if request.method == HTTPMethod.OPTIONS:
        response.response_content = json.dumps({})
        response.status = HTTPStatus.OK
        return response

    lat_lon = request.json.get("location", "") if request.json else ""

    latitude = lat_lon.split(",")[0]
    longitude = lat_lon.split(",")[1]

    geocode_result = googleService.geocoding(latitude, longitude)

    response.response_content = json.dumps({"localtion": geocode_result})

    return response


appv1 = Flask(__name__)
appv1.register_blueprint(flaskbp, url_prefix='/api/v1')
app.mount("/api/v1", WSGIMiddleware(appv1))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=[
        "./data",
        "./chat_data",
        "./.git"
    ], log_level="debug", use_colors=True)
