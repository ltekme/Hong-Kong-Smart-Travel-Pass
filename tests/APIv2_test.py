import unittest
from fastapi.testclient import TestClient

from APIv2App import app


class APIv2App_Test(unittest.TestCase):
    def setUp(self):
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


if __name__ == '__main__':
    unittest.main()
