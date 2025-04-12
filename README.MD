# Langchain-RestAPI-Framework

Orgionally this is a Langchain bot with a specific usecase, but at some point down the rabbit hole of adding feature to feature to feature, I found out I am no longer building a bot with a specific use case anymore. It has became a API wrapper for LLM.    

## Setup

### Enviroments

```.env
GOOGLE_API_KEY
GOOGLE_CSE_ID
GCP_AI_SA_CREDENTIAL_PATH='gcp_cred-ai.json'
CHATLLM_DB_URL='sqlite:///chat_data/chatLLM.db'
CHATLLM_ATTACHMENT_URL='./chat_data/messageAttachment'
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='upb'
OPENAI_API_URL
OPENAI_API_KEY
OPENAI_DPLY_NAME
OPENAI_API_VERSION
```

The enviroments above are just a template, set to specific values to match your usecase.

| Enviroment Variable | Description |
| - | - |
|GOOGLE_API_KEY| Google Cloud Maps API Key |
|GOOGLE_CSE_ID| The Google Custom Search Engine ID |
|GCP_AI_SA_CREDENTIAL_PATH | The GCP Vertex AI Service Account Key file location |
|CHATLLM_DB_URL | The SQLAlchemy database url for storing application data |
|CHATLLM_ATTACHMENT_URL| The dir for storing image attachments |

All path above are relative to /app.py in the project root.

### Why GCP

During the time of development, Google's GeminAI was used and kept as is.

### Setup Application

- install requirements

    ```sh
    pip install -r requirements.txt
    ```

- set env

    create a .env file in the same dir as this README.md file and set all paramaters in [#Enviroments](#Enviroments)

- create db

    ```sh
    python createDB.py
    ```

    run this script before starting any application

- build frontend

    view [Readme](l2dFrontend/README.md)

## Starting The APP

To run the app

```sh
python app.py
```

## Addittional Notes

- upgrade the db

    after setting envs, the DB need to be upgraded for anything v2 or after to function properly
    
    !!! important !!! make sure a copy of the DB exists before altering ORM Models and have alembic generate a revision

    ```sh
    alembic upgrade head
    ```

    run this command to upgrade the db

    ```sh
    alembic revision --autogenerate -m "revision"
    ```

    run this command to create a db revision
