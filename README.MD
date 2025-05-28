# Hong Kong Smart Travel Pass

## Enviroments and Tuneables

| Enviroment Variable          | Description                                              | Default                       |
| ---------------------------- | -------------------------------------------------------- | ----------------------------- |
| GOOGLE_API_KEY               | Google Cloud Maps API Key                                | --                            |
| GOOGLE_CSE_ID                | The Google Custom Search Engine ID                       | --                            |
| GCP_AI_SA_CREDENTIAL_PATH    | The GCP Vertex AI Service Account Key file location      | gcp_cred-ai.json              |
| CHATLLM_DB_URL               | The SQLAlchemy database url for storing application data | sqlite:///./chat_data/app.db  |
| CHATLLM_ATTACHMENT_URL       | The dir for storing image attachments                    | ./chat_data/messageAttachment |
| AZURE_OPENAI_API_KEY         |                                                          | --                            |
| AZURE_OPENAI_API_URL         |                                                          | --                            |
| AZURE_OPENAI_DEPLOYMENT_NAME |                                                          | --                            |
| AZURE_OPENAI_API_VERSION     |                                                          | --                            |
| USER_SESSION_EXPIRE_SECONDS  |                                                          | 7200                          |

All path above are relative to /app.py in the project root.

## Deployment

### Create Google Maps API

This is optional.

Please follow this guide and create an API Key

[https://developers.google.com/maps/documentation/javascript/get-api-key](https://developers.google.com/maps/documentation/javascript/get-api-key)

Assigne the key to the ENV: `GOOGLE_API_KEY`

### Create custom google search engine

This is optional.

Please go to the following page to create a programavle search engine.

[https://programmablesearchengine.google.com/controlpanel/all](https://programmablesearchengine.google.com/controlpanel/all)

Assigne the key to the ENV: `GOOGLE_CSE_ID`

### GCP Service Account

Please go to

[https://cloud.google.com/iam/docs/service-accounts-create](https://cloud.google.com/iam/docs/service-accounts-create)

to create a service accont and assign role to allow `aiplatform.endpoints.predict`

1. Put the json at the same location as the app.py

2. rename the json file to `gcp_cred-ai.json` or change the ENV: `GCP_AI_SA_CREDENTIAL_PATH` to the name of the json file.

### Fix openrice data

One of the tools uses openrice API, to do filtering the tool needs a few files

Enter the following links and save the file to path provided in the following table

| Link                                                                                                                                                           | path                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| [https://www.openrice.com/api/v2/metadata/region/all?uiLang=en&uiCity=hongkong](https://www.openrice.com/api/v2/metadata/region/all?uiLang=en&uiCity=hongkong) | ./data/openrice_raw.json          |
| [https://www.openrice.com/api/v2/metadata/country/all](https://www.openrice.com/api/v2/metadata/all)                                                           | ./data/openrice_metadata_raw.json |

The file should be just json, and it is, however for some reason the pathon `.decode()` function cannot decode it from bytes back to string for the json parcer

With the 2 file in place, the tool will not try to reach out to open rice server to get the 2 metadata content and try to fetch from the 2 file itself.

## Bring Up and Deployment

This is not mega-scaling production kind of ready. You can open it up to with WWW, but do it at your own risk.

```sh
docker compose up
```

adjust `docker-compose.yaml` as needed

It's a [Monolithic application](https://en.wikipedia.org/wiki/Monolithic_application), nothing wrong with it, simple and easy, just not 10k people spamming it all at once ready.
