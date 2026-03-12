import pytest_asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.core.media_storage import MEDIA_ROOT
from app.core.config import Config

from main import app  # 你的 FastAPI 实例


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    register_tortoise(
        app,
        config=Config().load_db_config(),
        generate_schemas=False
    )

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac

# 每个测试后清空表，保证隔离
@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    for model in Tortoise.apps["models"].values():
        await model.all().delete()
        
        