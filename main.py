from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from starlette.middleware.cors import CORSMiddleware

from app import user_router, auth_router, post_router, category_router
from app.core.media_storage import MEDIA_ROOT
from app.core.config import TiDBConfig, SQLiteConfig
from app.models import ServiceError

import uvicorn

MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

def get_main_app() -> FastAPI:
    app = FastAPI()

    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(post_router)
    app.include_router(category_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],  # 允许的源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    BASE_DIR = Path(__file__).parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    STATIC_DIR = FRONTEND_DIR / "static"

    app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")
    app.mount("/static/", StaticFiles(directory=str(STATIC_DIR)), name="frontend/static")

    register_tortoise(
        app,
        config=SQLiteConfig().load_db_config(),
        generate_schemas=False,
    )

    # 全局异常处理器，捕获 ServiceError 并返回 JSON 响应
    @app.exception_handler(ServiceError)
    async def service_error_handler(_: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


    @app.get("/", include_in_schema=False)
    async def home():
        return FileResponse(FRONTEND_DIR / "index.html")


    @app.get("/hello")
    async def hello():
        return {"message": "Hello World"}

    return app

app = get_main_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
