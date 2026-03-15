import pytest
import pytest_asyncio
import logging
from pathlib import Path

from tortoise import Tortoise
from fastapi.testclient import TestClient

#my code
from app.core import SQLiteConfig
from app.schemas import UserCreate, UserBrief, UserData, UserUpdate, UserChangePassword

from main import app

client = TestClient(app=app)

# 
ADMIN_USER = {
    "username": "ping",
    "password": "123123",
}

NORAML_USER_DICT = {
    "username": "zcr",
    "password": "123123",
    "email": "zcrisdog@qq.com",
    "description": "这是一个普通用户，就是畜生",
}

# 所有函数级别的测试前后都会执行这个 fixture，确保数据库连接正确初始化和关闭
@pytest_asyncio.fixture(autouse=True)
async def init_db():
    await Tortoise.init(config=SQLiteConfig().load_db_config())
    yield
    await Tortoise.close_connections()

@pytest.fixture(autouse=True)
def init_log():
    base_dir = Path(__file__).parent.parent
    log_dir = base_dir / "test/log/"
    log_dir.mkdir(parents=True, exist_ok=True)  # 确保日志目录存在    

    # 使用当前测试文件名生成日志，避免把绝对路径拼接进 log_dir
    log_file = log_dir / f"{Path(__file__).stem}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=str(log_file),
        force=True,
    )
    
    logging.info("测试开始")
    yield
    logging.info("测试结束")
    logging.shutdown()

@pytest.fixture
def admin_header() -> str:
    res = client.post("/auth/token", data={
        "username": "ping",
        "password": "123123",
    })
    assert res.status_code == 200, f"登录失败: {res.text}"
    
    header = {"Authorization": f"Bearer {res.json()['access_token']}"}
    return header


@pytest.fixture
def get_outh2_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# test main page
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

# test /user/detail 
def test_read_user_detail(admin_header):
    response = client.get("/user/detail", headers=admin_header)
    assert response.status_code == 200, f"/user/detail 获取失败: {response.text}"
    
    data = response.json()
    assert data["username"] == ADMIN_USER["username"]
    logging.info("/user/detail 测试通过，返回数据：%s", data)


# test /user/brief
def test_read_user_brief(admin_header):
    response = client.get("/user/brief", headers=admin_header)
    assert response.status_code == 200, f"/user/brief 获取失败: {response.text}"
    
    data = response.json()
    assert data["username"] == ADMIN_USER["username"]
    logging.info("/user/brief 测试通过，返回数据：%s", data)

