import os
import unittest
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from ChatLLMv2.GoogleServices import GoogleServices


load_dotenv('.env')

googleApiKey: str = os.environ.get("GOOGLE_API_KEY", "")
gcpServiceAccountPath: str = os.environ.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')


class GoogleService_Test(unittest.TestCase):

    def setUp(self):
        credentials = Credentials.from_service_account_file(gcpServiceAccountPath)  # type: ignore
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
        self.googleServices.apiKey = googleApiKey
        self.assertEqual(self.googleServices.geoLocationLookup(114.253441, 22.305710), "香港照鏡環景嶺路3號")

    def test_geoLocationLookup_invalidGeoCode(self):
        self.googleServices.apiKey = googleApiKey
        expectedExeception = "Cannot Perform Reverse Geocode Search due to errors"
        with self.assertRaises(Exception) as ve:
            self.googleServices.geoLocationLookup(-368, 132)
        self.assertEqual(str(ve.exception), expectedExeception)

    def test_geoLocationLookup_noApiKey(self):
        expectedExeception = "Config Error: Cannot Perform Reverse Geocode Search without API Key"
        with self.assertRaises(Exception) as ve:
            self.googleServices.geoLocationLookup(0, 0)
        self.assertEqual(str(ve.exception), expectedExeception)
