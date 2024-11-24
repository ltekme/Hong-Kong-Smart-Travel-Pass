import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    googleCSEId: str = os.environ.get("GOOGLE_CSE_ID", "")
    googleApiKey: str = os.environ.get("GOOGLE_API_KEY", "")
    gcpServiceAccountPath: str = os.environ.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')
    dbUrl: str = os.environ.get("CHATLLM_DB_URL", 'sqlite:///:memory:')
    attachmentDataPath: str = os.environ.get("CHATLLM_ATTACHMENT_URL", "./data/messageAttachment")


settings = Settings()
