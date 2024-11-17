import json
import base64
import os
from ChatLLM.gcpServices import GoogleServices

from google.oauth2.service_account import Credentials

credentialsFiles = list(filter(lambda f: f.startswith(
    'gcp_cred') and f.endswith('.json'), os.listdir('.')))
credentials = Credentials.from_service_account_file(  # type: ignore
    credentialsFiles[0])
googleService = GoogleServices(
    credentials,
    maps_api_key=os.getenv('GOOGLE_API_KEY')
)
bast_path = "./audio_data"

with open(bast_path + '/overide.json', encoding="utf-8") as f:
    conv_list = json.loads(f.read())

for conv in conv_list:
    message = conv["question"]
    sample_string_bytes = message.encode("utf-8")
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    print(f"Converting {message} to {base64_string}.wav")
    audio = googleService.speak(conv["response"].replace("#", ""))
    with open(f"{bast_path}/{base64_string}.wav", "w") as f:
        f.write(audio)
