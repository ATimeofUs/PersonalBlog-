import json
import logging
import subprocess
import pytest

from uuid import UUID
from app.schemas import UserCreate, UserUpdate, UserChangePassword

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def init_log(get_log_file):
	log_file = get_log_file("test_high_pressure")
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


@pytest.mark.asyncio
async def test_high_pressure_search():
    url = "http://127.0.0.1:8000/post/search?keyword=%25test&status=0&offset=1&limit=10"

    command = ["hey", "-n", "20000", "-c", "150", url]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # 打印结果以便查看响应时间分布
    logging.info("高压测试结果：%s", result.stdout)
    
    # 断言：如果 hey 返回状态码不为 0，说明测试工具本身运行出错
    assert result.returncode == 0


@pytest.mark.asyncio
async def test_high_pressure_create_user():
    url = "http://127.0.0.1:8000/user/create"
    
    post_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass",
        "description": "test description",
        "profile_photo": "test photo"
    }
    
    command = [
        "hey", "-n", "2000", "-c", "20", "-m", "POST",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(post_data), url
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    logging.info("高压测试结果：%s", result.stdout)
    
    assert result.returncode == 0

    """
    hey -n 2000 -c 20 -m POST -H "Content-Type: application/json" -d '{"username": "testuser", "email": "testuser@example.com", "password": "testpass", "description": "test description", "profile_photo": "test photo"}' http://127.0.0.1:8000/user/create
    
    """

