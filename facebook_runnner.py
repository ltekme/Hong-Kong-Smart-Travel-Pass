import getpass
import chat_llm_profile as cllmP

from google.oauth2.service_account import Credentials
import os
import json

if __name__ == "__main__":

    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)

    fb = cllmP.UserProfile.from_facebook_access_token(
        getpass.getpass("Enter Facebook Access Token: "),
        credentials,
        True
    )
    last_10 = fb.summory
    print(last_10)
