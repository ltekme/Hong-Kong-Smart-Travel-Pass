

## ENV to set

```.env
GOOGLE_API_KEY
GOOGLE_CSE_ID
GCP_AI_SA_CREDENTIAL_PATH='gcp_cred-ai.json'
GCP_DATA_SA_CREDENTIAL_PATH='gcp_cred-data.json'
CHATLLM_DB_URL='sqlite:///chat_data/chatLLM.db'
CHATLLM_ATTACHMENT_URL='./chat_data/messageAttachment'
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='upb'
```

this is the env template, the 2 at the top need to be populated

## Must do

- install requirements

    ```sh
    pip install -r requirements.txt
    ```

- create db

    ```sh
    python createDB.py
    ```

    run this script before starting any application

- pip install

    ```sh
    pip install -r requirements.txt
    ```

- set env

    create a .env file in the same dir as this README.md file and set all paramaters in [#ENV to set](#ENV-to-set)

- build frontend

    view [Readme](l2dFrontend/README.md)

## Note

To run the app

```sh
python app.py
```

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