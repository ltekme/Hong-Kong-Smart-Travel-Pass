import getpass
import ChatLLM.UserProfile as cllmP

from google.oauth2.service_account import Credentials
import os

if __name__ == "__main__":

    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)

    fb = cllmP.UserProfile.from_facebook_access_token(
        getpass.getpass("Enter Facebook Access Token: "),
        credentials,
        True
    )
    summ = fb.get_summory()
    print(summ)
    print("Save to file")
    print("Load from file")
    fb.save()
    summ = fb.get_summory()
    print(summ)
