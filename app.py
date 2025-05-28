import os
import uvicorn
from dotenv import load_dotenv

from APIv2 import app
from APIv2.dependence import dbEngine
from APIv2.modules import ApplicationModel
from fastapi.staticfiles import StaticFiles

load_dotenv('.env')


currentFilePath = os.path.dirname(os.path.realpath(__file__))
frontedFilePath = os.path.join(currentFilePath, "l2dFrontend")
fronendBuildPath = os.path.join(frontedFilePath, "build")

if fronendBuildPath and os.path.exists(fronendBuildPath):
    print(f"Mounting frontend build path: {fronendBuildPath}")
    app.mount("/", StaticFiles(directory=fronendBuildPath, html=True), name="frontend")

if __name__ == "__main__":
    target_metadata = ApplicationModel.TableBase.metadata
    target_metadata.create_all(dbEngine, checkfirst=True)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False, reload_excludes=[
        "./data",
        "./chat_data",
        "./.git",
        "./temp.py"
    ], log_level="debug", use_colors=True)
