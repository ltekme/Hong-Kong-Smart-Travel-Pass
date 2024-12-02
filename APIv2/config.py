import os
import logging
import typing as t
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    googleCSEId: str = os.environ.get("GOOGLE_CSE_ID", "")
    googleApiKey: str = os.environ.get("GOOGLE_API_KEY", "")
    gcpServiceAccountPath: str = os.environ.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')
    dbUrl: str = os.environ.get("CHATLLM_DB_URL", 'sqlite:///:memory:')
    attachmentDataPath: str = os.environ.get("CHATLLM_ATTACHMENT_URL", "./data/messageAttachment")

    sessionExpireInSeconds: int = 7200


class ClientCookiesKeys:
    SESSION_TOKEN: t.Final[str] = "sessionToken"


# uvicorn only stdout uvicorn.asgi, uvicorn.access, uvicorn.error
# see site-packages/uvicorn/config.py: 383-393
logger = logging.getLogger("uvicorn.asgi")
settings = Settings()
