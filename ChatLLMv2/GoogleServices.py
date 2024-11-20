import base64
import logging
import typing as t
from google.cloud.texttospeech import (
    TextToSpeechClient,
    VoiceSelectionParams,
    SynthesisInput,
    AudioConfig,
    AudioEncoding,
)
from google.cloud.speech import SpeechClient
from google.oauth2.service_account import Credentials


logger = logging.getLogger(__name__)


class GoogleServices:

    def __init__(self,
                 credentials: Credentials,
                 apiKey: str = "",
                 ) -> None:
        self.apiKey = apiKey
        self.ttsClient = TextToSpeechClient(credentials=credentials)
        self.sttClient = SpeechClient(credentials=credentials)

    def textToSpeech(self, text: str, lang: t.Literal["en", "zh"] = "zh") -> str:
        """output base64 audio representation of text"""
        logger.debug(f"Synthesis starting for {text}")
        voiceLangMapping = {
            "zh": VoiceSelectionParams(
                language_code="yue-HK",
                name="yue-HK-Standard-A",
            ),
            "en": VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Journey-F",
            )
        }
        synthesisText = SynthesisInput(text=text)
        audioConfig = AudioConfig(
            audio_encoding=AudioEncoding.LINEAR16,
            speaking_rate=1,
        )
        response = self.ttsClient.synthesize_speech({  # type: ignore
            "input": synthesisText,
            "voice": voiceLangMapping[lang],
            "audio_config": audioConfig,
        })
        base64AudioString = base64.b64encode(response.audio_content).decode("ascii")
        logger.debug(f'Speach to text response preview {base64AudioString[:20]=}')
        return base64AudioString
