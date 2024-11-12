from flask import Flask, request, render_template, Response
from flask_cors import CORS
import uuid
import json
import os
import base64

from gcp_tts import GoogleTTS

from google.oauth2.service_account import Credentials
# from hardcodequestion import CustomDict

from chat_llm import ChatLLM, MessageContentMedia, LLMChainModel, LLMChainTools
from langchain_google_vertexai import ChatVertexAI

credentialsFiles = list(filter(lambda f: f.startswith(
    'gcp_cred') and f.endswith('.json'), os.listdir('.')))
credentials = Credentials.from_service_account_file(
    credentialsFiles[0])
googleTTS = GoogleTTS(credentials)

app = Flask(__name__)
CORS(app)

#
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

UPLOAD_FOLDER = 'static/temporary'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent')
    if 'Mobile' in user_agent:
        return render_template('m_index.html')
    else:
        return render_template('index.html')


@app.route('/stt', methods=['POST'])
def get_sst():
    response = Response(
        content_type="application/json"
    )

    print("*" * 60)
    imageData = request.json.get('audioData')
    print("!" * 60)
    base64ImageData0 = imageData.split(',')[1]
    base64ImageData1 = base64.b64decode(base64ImageData0)

    text = GoogleTTS.speakToText(base64ImageData1)
    response.data = json.dumps({"message": text})
    print(response)

    return response


@app.route('/chat_api', methods=['POST'])
def get_information():
    response = Response(
        content_type="application/json"
    )

    no_data = {"no": "data"}
    request_json: dict = request.json or no_data
    content: dict = request_json.get('content', no_data)
    context: dict = request_json.get('context', no_data)
    message = content.get("message", "")
    images = content.get('images', [])

    # process context
    client_context = ""
    for co in context.keys():
        client_context += f"{co}: {context[co]}"

    # Expected images is a list of string containing src data url for image
    messageMedia = list(map(
        lambda img: MessageContentMedia.from_uri(img),
        images
    ))
    
    # Send to llm
    chatLLM.chatId = request_json.get('chatId', str(uuid.uuid4()))
    ai_response = chatLLM.new_message(
        message=message, media=messageMedia, context=client_context)

    print("3: " + ai_response.content.text)
    # audio = googleTTS.speak(ai_response.content.text)
    # print("audio: " + audio)
    response.data = json.dumps(
        {"message": ai_response.content.text, 
        #  "ttsAudio": audio,
         "chatId": chatLLM.chatId,
         })
    return response


@app.route('/api/geocode', methods=['POST'])
def get_geocoding():
    response = Response(
        content_type="application/json"
    )
    lat_lon = request.json.get("location") or ""

    latitude = lat_lon.split(",")[0]
    longitude = lat_lon.split(",")[1]

    geocode_result = googleTTS.geocoding(latitude, longitude)

    response.data = json.dumps({"localtion": geocode_result})

    return response


if __name__ == '__main__':
    print("Starting")
    # app.run(host="0.0.0.0", port=5000)
    app.run(debug=True)
