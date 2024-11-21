import unittest
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from ChatLLMv2.GoogleServices import GoogleServices
from APIv2.Config import (
    GCP_AI_SA_CREDENTIAL_PATH,
    GOOGLE_API_KEY
)

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

    def test_geoLocationLookup_HKDI(self):
        self.googleServices.apiKey = GOOGLE_API_KEY
        self.assertEqual(self.googleServices.geoLocationLookup(114.253441, 22.305710), "香港照鏡環景嶺路3號")

    def test_geoLocationLookup_invalidGeoCode(self):
        self.googleServices.apiKey = GOOGLE_API_KEY
        expectedExeception = "Cannot Perform Reverse Geocode Search due to errors"
        with self.assertRaises(Exception) as ve:
            self.googleServices.geoLocationLookup(-368, 132)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_geoLocationLookup_noApiKey(self):
        expectedExeception = "Cannot Perform Reverse Geocode Search without API Key"
        with self.assertRaises(Exception) as ve:
            self.googleServices.geoLocationLookup(0, 0)
        self.assertEqual(str(ve.exception), expectedExeception)
