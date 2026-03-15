import pytest
import pytest_asyncio
import logging
from pathlib import Path

from tortoise import Tortoise
from fastapi.testclient import TestClient

# my code
from app.core import SQLiteConfig
from app.schemas import UserCreate, UserBrief, UserData, UserUpdate, UserChangePassword
from app.models import User, UserLevel

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
    
    await User.filter(username__not=ADMIN_USER["username"]).delete()
    
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

    # 清空日志文件内容，确保每次测试都是干净的日志
    log_file.write_text("")

    logging.info("测试开始")
    yield
    logging.info("测试结束")
    logging.shutdown()


@pytest.fixture
def admin_header() -> str:
    res = client.post(
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


# test /user/change_password
def test_change_password(admin_header):
    change_data = UserChangePassword(
        new_password="123123+",
        old_password="123123",
    )

    response = client.post(
        "/user/change_password", headers=admin_header, json=change_data.model_dump()
    )

    assert response.status_code == 200, (
        f"/user/change_password 修改失败: {response.text}"
    )

    change_data = UserChangePassword(
        new_password="123123",
        old_password="123123+",
    )

    response = client.post(
        "/user/change_password", headers=admin_header, json=change_data.model_dump()
    )

    assert response.status_code == 200, (
        f"/user/change_password 修改失败: {response.text}"
    )
    logging.info("/user/change_password 测试通过，密码已修改并恢复")


# test /user/update
def test_update_user(admin_header):
    update_data = UserUpdate(
        email="220340119@cauc.edu.cn",
        description="这是管理员用户",
    )

    response = client.post(
        "/user/update", headers=admin_header, json=update_data.model_dump()
    )

    assert response.status_code == 200, f"/user/update 修改失败: {response.text}"

    data = response.json()
    assert data["email"] == update_data.email
    assert data["description"] == update_data.description
    logging.info("/user/update 测试通过，返回数据：%s", data)


# test /user/avatar
def test_upload_avatar(admin_header):
    # 这里我们使用一个小的测试图片，确保它存在于测试目录中
    test_image_path = "/home/ping/Pictures/other/A-sir.png"

    with open(test_image_path, "rb") as img_file:
        files = {"avatar": ("test_avatar.png", img_file, "image/png")}
        response = client.post("/user/avatar", headers=admin_header, files=files)

    logging.info("/user/avatar 上传测试通过 %s", response.text)

    assert response.status_code == 200, f"/user/avatar 上传失败: {response.text}"

    data = response.json()
    logging.info("/user/avatar 测试通过，返回数据：%s", data)


# test /user/show_user
def test_show_user(admin_header):
    response = client.get(
        "/user/show_user",
        headers=admin_header,
        # params={"limit" : 10, "offset": 0} 可选
    )

    assert response.status_code == 200, f"/user/show_user 获取失败: {response.text}"

    data = response.json()

    assert isinstance(data, list), "返回数据应为用户列表"

    logging.info("/user/show_user 测试通过，返回数据：%s", data)


# test /user/delete_user
def test_delete_user(admin_header):
    # 首先创建一个临时用户用于删除测试
    temp_user_data = UserCreate(
        username="temp_user", password="temp_pass", email="1asdfasdf@qq.com"
    )

    create_response = client.post(
        "/user/create_user", headers=admin_header, json=temp_user_data.model_dump()
    )
    assert create_response.status_code == 200, (
        f"创建临时用户失败: {create_response.text}"
    )

    temp_user_id = create_response.json()["id"]

    # 现在删除这个临时用户
    delete_response = client.post(
        "/user/delete_user", headers=admin_header, json={"user_id": temp_user_id}
    )
    assert delete_response.status_code == 200, (
        f"/user/delete_user 删除失败: {delete_response.text}"
    )


# test /user/upgrade_user_level
def test_upgrade_user_level(admin_header):
    # 首先创建一个临时用户用于升级测试
    temp_user_data = UserCreate(
        username="temp_user2", password="temp_pass2", email="123123123@qq.com"
    )

    create_response = client.post(
        "/user/create_user", headers=admin_header, json=temp_user_data.model_dump()
    )
    assert create_response.status_code == 200, (
        f"创建临时用户失败: {create_response.text}"
    )

    temp_user_id = create_response.json()["id"]

    # 现在升级这个临时用户
    upgrade_response = client.post(
        "/user/upgrade_user_level", headers=admin_header, json={"user_id": temp_user_id}
    )
    assert upgrade_response.status_code == 200, (
        f"/user/upgrade_user_level 升级失败: {upgrade_response.text}"
    )


