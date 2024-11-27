import uvicorn
import logging
from APIv2 import *

if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
