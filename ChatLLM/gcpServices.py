import os
import requests
import base64
from google.cloud import texttospeech, speech
from google.oauth2 import service_account


class GoogleServices:

    verbose = False

    def logger(self, msg: str):
        # \033[92m
        if self.verbose:
            print("\033[92m[gcpService]" + str(msg) + "\033[0m")

    def __init__(self,
                 credentials: service_account.Credentials,
                 maps_api_key: str | None = None,
                 verbose: bool = False,
                 ) -> None:
        self.maps_api_key = maps_api_key
        self.verbose = verbose
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
        self.sstCredentials = speech.SpeechClient(credentials=credentials)

    def speak(self, textData: str) -> str:
        self.logger(f"Synthesis starting for {textData}")
        input_text = texttospeech.SynthesisInput(text=textData)
        response = self.client.synthesize_speech(
            request={"input": input_text, "voice": self.voice,
                     "audio_config": self.audio_config}
        )
        base64EncodedStr = base64.b64encode(response.audio_content)
        self.logger(f'Speach to text response preview {base64EncodedStr[:10]=}')
        return base64EncodedStr.decode('utf-8')

    def speakToText(self, wav):
        self.logger(f"Staring Recognition for {wav[:10]=}")
        audio_file = speech.RecognitionAudio(content=wav)
        config = speech.RecognitionConfig(
            enable_automatic_punctuation=True,
            enable_spoken_emojis=False,
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code='yue-Hant-HK',
            alternative_language_codes=['en-US', 'yue-Hant-HK'],  # 'cmn-Hans-CN'
            use_enhanced=True,
        )
        response = self.sstCredentials.recognize(
            config=config,
            audio=audio_file
        )
        transcript = ''
        for result in response.results:
            transcript += result.alternatives[0].transcript
        self.logger(f"Finish Recognition for {wav[:10]=} got {transcript[:10]=}")
        return transcript

    def geocoding(self, latitude, longitude):
        self.logger(f"querying geocoding api for {latitude=},{longitude=}")
        url = "https://maps.googleapis.com/maps/api/geocode/json?language=zh-HK&latlng={},{}&key={}".format(
            latitude, longitude, self.maps_api_key
        )
        response = requests.get(url)
        localtion = ""
        try:
            if response.status_code == 200:
                data = response.json()
                self.logger(f"Response Data1: {data}", )
                localtion = data['results'][1]['formatted_address'][2:]
                self.logger(f"Response Data2: {localtion}")
            else:
                self.logger(f"Error: {response.status_code}, {response.text}")
            return localtion
        except Exception as e:
            self.logger(f"Error getting geo data {e}")
            return "Error getting data"


if __name__ == "__main__":
    credentials = service_account.Credentials.from_service_account_file(
        './Key.json')
    googleTTS = GoogleServices(
        credentials,
        maps_api_key=os.getenv("GOOGLE_API_KEY"))
    resault = googleTTS.speak('Hello')
    print(resault)
