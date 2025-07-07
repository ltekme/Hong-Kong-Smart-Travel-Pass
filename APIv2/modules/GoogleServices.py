import base64
import googlemaps  # type: ignore
import typing as t
import sqlalchemy.orm as so

from google.cloud.texttospeech import TextToSpeechClient
from google.cloud.texttospeech import VoiceSelectionParams
from google.cloud.texttospeech import SynthesisInput
from google.cloud.texttospeech import AudioConfig
from google.cloud.texttospeech import AudioEncoding
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types.cloud_speech import RecognitionConfig
from google.cloud.speech_v2.types.cloud_speech import AutoDetectDecodingConfig
from google.cloud.speech_v2.types.cloud_speech import RecognitionFeatures
from google.cloud.speech_v2.types.cloud_speech import RecognizeRequest
from google.oauth2.service_account import Credentials

from ..logger import logger
from .Services.PermissionAndQuota.Quota import QuotaService
from .Services.PermissionAndQuota.Permission import PermissionService
from .Services.PermissionAndQuota.ServiceBase import ServiceWithAAA
from .ApplicationModel import User
from .exception import ConfigurationError

MAX_AUDIO_LENGTH_SECS = 8 * 60 * 60


class GoogleServices(ServiceWithAAA):
    """Service class for interacting with Google Cloud's Text-to-Speech and Speech-to-Text APIs."""

    def __init__(self,
                 dbSession: so.Session,
                 quotaService: QuotaService,
                 permissionService: PermissionService,
                 user: t.Optional[User] = None,
                 credentials: t.Optional[Credentials] = None,
                 apiKey: str | None = "",
                 ) -> None:
        """
        Initialize a GoogleServices instance.

        :param credentials: The Google Cloud credentials.
        :param apiKey: The API key for Google Cloud services.
        """
        super().__init__(dbSession, "Google Service", quotaService=quotaService, permissionService=permissionService, user=user)
        self.apiKey = apiKey
        if not credentials:
            logger.warning(f'Google Service Credentials not present, may lead to errors if client is not set up')
        self.ttsClient = TextToSpeechClient(credentials=credentials)
        self.sttClient = SpeechClient(credentials=credentials)
        self.projectID = str(credentials.project_id if credentials is not None else "")  # type: ignore

    def textToSpeech(self, text: str, lang: t.Literal["en", "zh"] = "zh") -> str:
        """
        Convert text to speech and return the base64 encoded audio representation.

        :param text: The text to convert to speech.
        :param lang: The language of the text ("en" for English, "zh" for Chinese).
        :return: The base64 encoded audio representation of the text.
        """
        logger.debug(f"Synthesis starting for {text[10:]=}")
        try:
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
        except Exception as e:
            logger.error(f'Cannot synthesise text {e}, returning empty string.')
            return ""

    def geoLocationLookup(self, longitude: float, latitude: float, lang: str = "zh-HK") -> str:
        """
        Perform location lookup for given longitude and latitude value.

        :param longitude: The longitude of the location to lookup.
        :param latitude: The longitude of the location to lookup.
        :return: The location string of the given longitude and latitude value.
        """
        logger.debug(f'Performing location lookup for {longitude=},{latitude=},{lang=}')
        if not self.apiKey:
            logger.warning(f'API Key not present, cannot perform lookup')
            raise ConfigurationError("Cannot Perform Reverse Geocode Search without API Key")
        try:
            # This works, it not our fault that this works but not show up on editors
            maps = googlemaps.Client(key=self.apiKey)
            resault = maps.reverse_geocode(latlng=(latitude, longitude), language=lang)  # type: ignore
            location = str(resault[1]['formatted_address'])  # type: ignore
            logger.debug(f"Got location of {location} from ({longitude},{latitude})")
            return location
        except Exception as e:
            logger.error(f"Cannot Perform Reverse Geocode Search: {e}")
            raise Exception("Cannot Perform Reverse Geocode Search due to errors")

    def speechToText(self, audioData: str) -> str:
        """
        Convert speech to text

        :param audioData: The base64 encoded audio data to convert to text.
        :param lang: The language of the audio data ("zh-HK" for Cantonese, "en-US" for English).
        :return: The text representation of the audio data.
        """
        if not self.projectID:
            self.loggerError(f'Cannot process {audioData[:20]=} for STT, Empty Project ID')
            raise ConfigurationError()
        try:
            audioContent = base64.b64decode(audioData)
            logger.debug(f'Starting text regization for audioData {audioData[:20]=}')
            config = RecognitionConfig(
                auto_decoding_config=AutoDetectDecodingConfig(),
                features=RecognitionFeatures(
                    enable_word_confidence=False,
                    enable_word_time_offsets=False,
                ),
                model="long",
                language_codes=["yue-Hant-HK"],
            )
            request = RecognizeRequest(
                recognizer=f"projects/{self.projectID}/locations/global/recognizers/_",
                config=config,
                content=audioContent,
            )
            operation = self.sttClient.recognize(request=request)  # type: ignore
            resault = operation.results
            if len(resault) < 1:
                logger.debug(f"No resault from {audioData[:20]=} got {resault=}")
                return ""
            response = resault[-1].alternatives[-1].transcript
            # leanth = resault[-1].result_end_offset.seconds # Useful for accounting and qoutering
            logger.debug(f"Finish Recognition for {audioData[:20]=} got {resault=}")
            return response
        except Exception as e:
            self.loggerError(f"Error processing Recognition {e}")
            return ""
