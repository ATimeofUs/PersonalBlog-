import pytest
import pytest_asyncio
import logging
from pathlib import Path

from tortoise import Tortoise

# my code
from app.core import SQLiteConfig, TiDBConfig
from app.models import User, Post, Category  
from main import app

from httpx import AsyncClient, ASGITransport

ADMIN_USER = {
    "username": "ping",
    "password": "123123",
}

POST_TEST = {
    "title": "测试文章",
    "content": "这是测试文章的内容",
    "category_id": 1,  # 假设分类 ID 1 已存在
}

CATEGORY_TEST = {
    "name": "测试分类",
    "description": "这是测试分类的描述",
} 

# init

NOW_DIR = Path(__file__).parent

@pytest.fixture(scope="session")
def get_log_file():
    def _get_log_file(log_file_name: str):
        base_dir = NOW_DIR
        log_dir = base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{log_file_name}.log"
        log_file.write_text("")
        return log_file
    return _get_log_file


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)

    # 使用 ASGITransport 创建 AsyncClient，确保测试环境与实际运行环境一致
    # base_url 可以设置为 "http://test"，因为 ASGITransport 不会真正发出 HTTP 请求，而是直接调用 FastAPI 应用
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# 所有函数级别的测试前后都会执行这个 fixture，确保数据库连接正确初始化和关闭
@pytest_asyncio.fixture(autouse=True, scope="session")
async def init_db():
    await Tortoise.init(config=TiDBConfig().load_db_config())
    yield
    
    await User.filter(username__not=ADMIN_USER["username"]).delete()
    await Post.all().delete()
    await Category.all().delete()
    
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def admin_header(async_client) -> dict:
    res = await async_client.post(
        "/auth/token",
        data={
            "username": "ping",
            "password": "123123",
        },
    )
    assert res.status_code == 200, f"登录失败: {res.text}"

    header = {"Authorization": f"Bearer {res.json()['access_token']}"}
    return header


@pytest.fixture
def get_outh2_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
