import os
from llm_tools.Openrice.caller import *
from google.oauth2.service_account import Credentials

credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

kwargs = {
    "verbose": True,
    "credentials": credentials
}
print(LandmarkFilter(**kwargs).all[0])
print(DistrictFilter(**kwargs).all[0])
print(CuisineFilter(**kwargs).all[0])
print(DishFilter(**kwargs).all[0])
print(ThemeFilter(**kwargs).all[0])
print(AmenityFilter(**kwargs).all[0])
print(PriceRangeFilter(**kwargs).all[0])