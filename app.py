import os
import uvicorn
from dotenv import load_dotenv

from APIv2 import app
from fastapi.staticfiles import StaticFiles

load_dotenv('.env')


currentFilePath = os.path.dirname(os.path.realpath(__file__))
frontedFilePath = os.path.join(currentFilePath, "l2dFrontend")
fronendBuildPath = os.path.join(frontedFilePath, "build")

if fronendBuildPath and os.path.exists(fronendBuildPath):
    app.mount("/static", StaticFiles(directory=fronendBuildPath), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=[
        "./data",
        "./chat_data",
        "./.git",
        "./temp.py"
    ], log_level="debug", use_colors=True)
