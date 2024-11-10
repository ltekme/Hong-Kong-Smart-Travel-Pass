import getpass
import chat_llm_profile as cllmP

import json

if __name__ == "__main__":
    fb = cllmP.UserProfile.from_facebook_access_token(
        getpass.getpass("Enter Facebook Access Token: ")
    )
    last_10 = fb.get_user_details()
    print(json.dumps(last_10, indent=4))
