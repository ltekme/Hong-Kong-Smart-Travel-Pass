import getpass
import chat_llm_profile as cllmP

if __name__ == "__main__":
    fb = cllmP.UserProfile.from_facebook_access_token(
        getpass.getpass("Enter Facebook Access Token: ")
    )
    print(fb)
