from google.cloud import texttospeech, speech
from google.oauth2 import service_account
import google.generativeai as genai
import os
import dotenv
import requests

import base64

dotenv.load_dotenv()


class GoogleServices:

    def __init__(self,
                 credentials: service_account.Credentials,
                 maps_api_key: str | None = None
                 ) -> None:
        self.maps_api_key = maps_api_key

        self.client = texttospeech.TextToSpeechClient(
            credentials=credentials
        )
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="yue-HK",
            name="yue-HK-Standard-A",
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1
        )

        self.model = genai.GenerativeModel("gemini-1.5-flash")

        self.sstCredentials = speech.SpeechClient(credentials=credentials)

    def speak(self, textData: str) -> str:
        input_text = texttospeech.SynthesisInput(text=textData)

        response = self.client.synthesize_speech(
            request={"input": input_text, "voice": self.voice,
                     "audio_config": self.audio_config}
        )

        base64EncodedStr = base64.b64encode(response.audio_content)
        print('base64url', base64EncodedStr)
        return base64EncodedStr.decode('utf-8')

    def speakToText(self, wav):

        audio_file = speech.RecognitionAudio(content=wav)

        config = speech.RecognitionConfig(
            enable_automatic_punctuation=True,
            enable_spoken_emojis=False,
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code='yue-Hant-HK',
            alternative_language_codes=['en-US', 'yue-Hant-HK, '],  # 'cmn-Hans-CN'
            use_enhanced=True,
        )
        response = self.sstCredentials.recognize(
            config=config,
            audio=audio_file
        )
        transcript = ''
        for result in response.results:
            transcript += result.alternatives[0].transcript
        print(transcript)
        return transcript

    def geocoding(self, latitude, longitude):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?language=zh-HK&latlng={
            latitude},{longitude}&key={self.maps_api_key}"
        print("Url", url)
        response = requests.get(url)
        print(response)
        if response.status_code == 200:
            data = response.json()
            print("Response Data1:", data)

            localtion = data['results'][1]['formatted_address'][2:]
            print("Response Data2:", localtion)

        else:
            print("Error:", response.status_code, response.text)
        return localtion


if __name__ == "__main__":
    credentials = service_account.Credentials.from_service_account_file(
        './Key.json')
    googleTTS = GoogleServices(
        credentials,
        maps_api_key=os.getenv("GOOGLE_API_KEY"))
    resault = googleTTS.speak('Hello')
    print(resault)
