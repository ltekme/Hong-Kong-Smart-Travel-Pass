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


if __name__ == '__main__':
    unittest.main()
