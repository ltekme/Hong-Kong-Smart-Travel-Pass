## Note

run [APIv2_config.py](APIv2_config.py) to init db before running [APIv2.py](APIv2.py)

```sh
python ./APIv2_config.py
fastapi  dev ./APIv2.py 
```

after runing [APIv2_config.py](APIv2_config.py) for the first time as long as the DB is not delete, this script does not need to be run again when starting the API server


## ENV to set

GOOGLE_API_KEY
GOOGLE_CSE_ID
CHATLLM_DB_PATH='./data/chatLLM.db'
GCP_AI_SA_CREDENTIAL_PATH='gcp_cred-ai.json'
GCP_DATA_SA_CREDENTIAL_PATH='gcp_cred-data.json'
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='python'