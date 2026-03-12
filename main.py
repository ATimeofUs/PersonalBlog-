from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from tortoise.contrib.fastapi import register_tortoise

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router

from app.core.media_storage import MEDIA_ROOT
from app.core.config import Config

# ============ FastAPI 应用初始化 ============


MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.include_router(user_router)
app.include_router(auth_router)

app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

register_tortoise(
	app,
	config=Config().load_db_config(),
	generate_schemas=False, # 不自动生成数据库表结构，改为手动管理迁移
)


@app.get("/")
async def main_route():
	return {"hello": "world"}


if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
