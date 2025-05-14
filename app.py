# this is examed from unitest as this will be depracted
import os
import json
import base64
import uvicorn
from dotenv import load_dotenv

from APIv2 import app
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles

from flask import Flask, request, Response, Blueprint
from http import HTTPStatus, HTTPMethod
from google.oauth2.service_account import Credentials
from ChatLLM.gcpServices import GoogleServices

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

currentFilePath = os.path.dirname(os.path.realpath(__file__))
frontedFilePath = os.path.join(currentFilePath, "l2dFrontend")
fronendBuildPath = os.path.join(frontedFilePath, "build")

appv1 = Flask(__name__)


@flaskbp.route('/stt', methods=[HTTPMethod.POST, HTTPMethod.OPTIONS])
def get_sst():
    response = Response(headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Max-Age': '300',
                        "Content-Type": "application/json",
                        })

    if request.method == HTTPMethod.OPTIONS:
        response.data = json.dumps({})
        response.status = HTTPStatus.OK
        return response

    imageData = request.json.get('audioData') if request.json else ""
    base64ImageData0 = imageData.split(',')[1]
    base64ImageData1 = base64.b64decode(base64ImageData0)
    text = googleService.speakToText(base64ImageData1)
    response.data = json.dumps({"message": text})
    return response


appv1.register_blueprint(flaskbp, url_prefix='/api/v1')
app.mount("/api/v1", WSGIMiddleware(appv1))

if fronendBuildPath and os.path.exists(fronendBuildPath):
    app.mount("/static", StaticFiles(directory=fronendBuildPath), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=[
        "./data",
        "./chat_data",
        "./.git"
    ], log_level="debug", use_colors=True)
