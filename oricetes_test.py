import os
import llm_tools.Openrice.caller as openrice
from google.oauth2.service_account import Credentials

credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

kwargs = {
    "verbose": True,
    "credentials": credentials
}
filters = openrice.Filters(**kwargs)
resault = filters.search("kowloon bay")
print("\n".join(resault))
