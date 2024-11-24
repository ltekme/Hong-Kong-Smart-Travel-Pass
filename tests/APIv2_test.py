import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from google.oauth2.service_account import Credentials

from APIv2 import app
from APIv2.dependence import (
    getSession,
    getGoogleService,
)
from ChatLLMv2.ChatManager import TableBase
from ChatLLMv2.GoogleServices import GoogleServices


envValues = dotenv_values('.env')
apiKey = envValues.get("GOOGLE_API_KEY", "")
gcpServiceAccountPath = envValues.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(gcpServiceAccountPath)  # type: ignore


class APIv2App_Test(unittest.TestCase):
    dbPath = "data/testing.db"

    def setUp(self):
        # Testing should be done from the folder outside tests
        # All of these unitest are only working with vscode unitesting function
        # The create_engine starting path is outuide the tests folders
        engine = sa.create_engine(
            url=f"sqlite:///{self.dbPath}",
            connect_args={"check_same_thread": False}
        )
        TableBase.metadata.create_all(engine)
        with so.Session(engine) as session:
            def getSessionOveride():
                return session

        app.dependency_overrides[getSession] = getSessionOveride
        self.client = TestClient(app)

    def test_chatLLM_full_input(self):
        response = self.client.post("/chatLLM", json={
            "chatId": "abc",
            "content": {
                "message": "hello",
                "media": [
                    "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
                ]
            },
            "context": {
                "currentTime": "11:00 - 20/11/2024",
            }
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chatId"], "abc")
        self.assertGreater(len(response.json()["message"]), 3)

    def test_chatLLM_invalid_attachment(self):
        response = self.client.post("/chatLLM", json={
            "chatId": "abc",
            "content": {
                "message": "hello",
                "media": [
                    "abcd:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
                ]
            },
            "context": {
                "currentTime": "11:00 - 20/11/2024",
            }
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid Image Provided")

    def test_chatLLM_noDisable_tts(self):
        response = self.client.post("/chatLLM", json={
            "chatId": "abc",
            "content": {
                "message": "hello12354"
            }
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()["ttsAudio"]), 3)

    def test_chatLLM_disable_tts(self):
        response = self.client.post("/chatLLM", json={
            "chatId": "abc",
            "content": {
                "message": "hello12354"
            },
            "disableTTS": True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ttsAudio"]), 0)

    def test_geocode_no_api_key(self):
        def getGoogleServiceOveride():
            return GoogleServices(
                credentials=credentials,
                apiKey=""
            )
        app.dependency_overrides[getGoogleService] = getGoogleServiceOveride
        client = TestClient(app)
        response = client.post("/geocode", json={
            "latitude": 114.253441,
            "longitude": 22.305710,
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Cannot perform geolocation lookup")

    def test_geocode_invalid_geocode(self):
        if apiKey is None:
            self.fail("API key is not set")
        googleServices = GoogleServices(
            credentials=credentials,
            apiKey=apiKey
        )

        def getGoogleServiceOveride():
            return googleServices
        app.dependency_overrides[getGoogleService] = getGoogleServiceOveride
        client = TestClient(app)
        response = client.post("/geocode", json={
            "latitude": -368,
            "longitude": 132,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Error performing geolocation lookup")

    def test_geocode_valid(self):
        if apiKey is None:
            self.fail("API key is not set")
        googleServices = GoogleServices(
            credentials=credentials,
            apiKey=apiKey
        )

        def getGoogleServiceOveride():
            return googleServices
        app.dependency_overrides[getGoogleService] = getGoogleServiceOveride
        client = TestClient(app)
        response = client.post("/geocode", json={
            "longitude": 114.253441,
            "latitude": 22.305710,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["location"], "香港照鏡環景嶺路3號")


if __name__ == '__main__':
    unittest.main()
