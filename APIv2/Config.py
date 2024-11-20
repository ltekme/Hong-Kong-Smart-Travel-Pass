import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")
GCP_AI_SA_CREDENTIAL_PATH = os.environ.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')
GCP_DATA_SA_CREDENTIAL_PATH = os.environ.get("GCP_DATA_SA_CREDENTIAL_PATH", 'gcp_cred-data.json')
CHATLLM_DB_URL = os.environ.get("CHATLLM_DB_URL", 'sqlite:///:memory:')
CHATLLM_ATTACHMENT_URL = os.environ.get("CHATLLM_ATTACHMENT_URL", "./data/messageAttachment")
