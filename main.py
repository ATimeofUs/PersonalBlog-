from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from tortoise.contrib.fastapi import register_tortoise

from app import user_router, auth_router, post_router, category_router
from app.core.media_storage import MEDIA_ROOT
from app.core.config import Config


MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(post_router)
app.include_router(category_router)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    config=Config().load_db_config(),
    generate_schemas=False,
)

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(TEMPLATES_DIR / "index.html")

@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)