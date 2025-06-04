import os
import sqlalchemy as sa
from dotenv import load_dotenv
from APIv2.modules.ApplicationModel import TableBase 

load_dotenv('.env')

dbUrl = os.environ.get("CHATLLM_DB_URL", "sqlite:///./chat_data/app.db")

if dbUrl.startswith("sqlite:///"):
    dbFile = dbUrl.replace("sqlite:///", "./")
    if not os.path.exists(os.path.dirname(dbFile)):
        os.makedirs(os.path.dirname(dbFile))

TableBase.metadata.create_all(sa.create_engine(url=dbUrl))
