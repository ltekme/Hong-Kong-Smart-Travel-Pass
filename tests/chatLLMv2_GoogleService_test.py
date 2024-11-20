import unittest
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from ChatLLMv2.GoogleServices import GoogleServices
from APIv2.Config import GCP_AI_SA_CREDENTIAL_PATH

load_dotenv('.env')


class GoogleService_Test(unittest.TestCase):

    def setUp(self):
        credentials = Credentials.from_service_account_file(GCP_AI_SA_CREDENTIAL_PATH)  # type: ignore
        self.googleServices = GoogleServices(credentials=credentials)

    def test_textToSpeech_en(self):
        text = "Hello World! In English"
        audioDataString = self.googleServices.textToSpeech(text, 'en')
        self.assertIsNotNone(audioDataString)

    def test_textToSpeech_zh(self):
        text = "你好世界"
        audioDataString = self.googleServices.textToSpeech(text, 'zh')
        self.assertIsNotNone(audioDataString)
