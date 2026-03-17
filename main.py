from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise
from contextlib import asynccontextmanager

from app import user_router  
from app import auth_router  
from app import post_router  
from app import category_router
from app.core.media_storage import MEDIA_ROOT
from app.core import SQLiteConfig

import uvicorn

# 使用 asynccontextmanager 的全局数据管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 防止循环import，放在函数内部
    from app.core import redis_manager
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    await Tortoise.init(config=SQLiteConfig().load_db_config())
    await redis_manager.init_redis_pool()
    yield
    await redis_manager.close_redis_pool()
    await Tortoise.close_connections()
    

def create_app() -> FastAPI:
    app_instance = FastAPI(lifespan=lifespan)

    app_instance.include_router(user_router)
    app_instance.include_router(auth_router)
    app_instance.include_router(post_router)
    app_instance.include_router(category_router)

    BASE_DIR = Path(__file__).parent
    STATIC_DIR = BASE_DIR / "static"

    app_instance.mount("/assets/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")
    app_instance.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app_instance.get("/")
    async def home():
        return {"message": "Welcome to the Personal Blog API! Please use the /docs endpoint to explore the API documentation."}
        
    return app_instance


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

