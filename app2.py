from fastapi import FastAPI, APIRouter

app = FastAPI()

router = APIRouter(prefix="/chatLLM")


@router.post("/")
def home():
    return "hello"


app.include_router(router)
