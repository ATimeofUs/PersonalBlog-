import pytest
import logging
import time
# my code
from .conftest import ADMIN_USER
from app.schemas import UserCreate, UserUpdate, UserChangePassword
from app.models import User, UserLevel

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def init_log(get_log_file):
    log_file = get_log_file("test_user")
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



# test main page
async def test_read_main(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200


# test /user/detail
async def test_read_user_detail(async_client, admin_header):
    response = await async_client.get("/user/detail", headers=admin_header)
    assert response.status_code == 200, f"/user/detail 获取失败: {response.text}"

    data = response.json()
    assert data["username"] == ADMIN_USER["username"]
    logging.info("/user/detail 测试通过，返回数据：%s", data)


# test /user/brief
async def test_read_user_brief(async_client, admin_header):
    response = await async_client.get("/user/brief", headers=admin_header)
    assert response.status_code == 200, f"/user/brief 获取失败: {response.text}"

    data = response.json()
    assert data["username"] == ADMIN_USER["username"]
    logging.info("/user/brief 测试通过，返回数据：%s", data)


# test /user/change_password
async def test_change_password(async_client, admin_header):
    change_data = UserChangePassword(
        new_password="123123+",
        old_password="123123",
    )

    response = await async_client.post(
        "/user/change_password", headers=admin_header, json=change_data.model_dump()
    )

    assert response.status_code == 200, (
        f"/user/change_password 修改失败: {response.text}"
    )

    change_data = UserChangePassword(
        new_password="123123",
        old_password="123123+",
    )

    response = await async_client.post(
        "/user/change_password", headers=admin_header, json=change_data.model_dump()
    )

    assert response.status_code == 200, (
        f"/user/change_password 修改失败: {response.text}"
    )
    logging.info("/user/change_password 测试通过，密码已修改并恢复")


# test /user/update
async def test_update_user(async_client, admin_header):
    update_data = UserUpdate(
        email="220340119@cauc.edu.cn",
        description="这是管理员用户",
    )

    response = await async_client.post(
        "/user/update", headers=admin_header, json=update_data.model_dump()
    )

    assert response.status_code == 200, f"/user/update 修改失败: {response.text}"

    data = response.json()
    assert data["email"] == update_data.email
    assert data["description"] == update_data.description
    logging.info("/user/update 测试通过，返回数据：%s", data)


# test /user/avatar
async def test_upload_avatar(async_client, admin_header):
    # 这里我们使用一个小的测试图片，确保它存在于测试目录中
    test_image_path = "/home/ping/Pictures/other/A-sir.png"

    with open(test_image_path, "rb") as img_file:
        files = {"avatar": ("test_avatar.png", img_file, "image/png")}
        response = await async_client.post("/user/avatar", headers=admin_header, files=files)

    logging.info("/user/avatar 上传测试通过 %s", response.text)

    assert response.status_code == 200, f"/user/avatar 上传失败: {response.text}"

    data = response.json()
    logging.info("/user/avatar 测试通过，返回数据：%s", data)


# test /user/show
async def test_show_user(async_client, admin_header):
    response = await async_client.get(
        "/user/show",
        headers=admin_header,
        # params={"limit" : 10, "offset": 0} 可选
    )

    assert response.status_code == 200, f"/user/show 获取失败: {response.text}"

    data = response.json()

    assert isinstance(data, list), "返回数据应为用户列表"

    logging.info("/user/show 测试通过，返回数据：%s", data)


# test /user/delete
async def test_delete(async_client, admin_header):
    # 首先创建一个临时用户用于删除测试
    temp_user_data = UserCreate(
        username="temp_user", password="temp_pass", email="1asdfasdf@qq.com"
    )

    create_response = await async_client.post(
        "/user/create", headers=admin_header, json=temp_user_data.model_dump()
    )
    assert create_response.status_code == 200, (
        f"创建临时用户失败: {create_response.text}"
    )

    temp_user_id = create_response.json()["id"]

    # 现在删除这个临时用户
    delete_response = await async_client.post(
        "/user/delete", headers=admin_header, json={"user_id": temp_user_id}
    )
    assert delete_response.status_code == 200, (
        f"/user/delete 删除失败: {delete_response.text}"
    )


# test /user/upgrade_level
async def test_upgrade_level(async_client, admin_header):
    # 首先创建一个临时用户用于升级测试
    temp_user_data = UserCreate(
        username="temp_user2", 
        password="temp_pass2", 
        email="123123123@qq.com"
    )

    create_response = await async_client.post(
        "/user/create", 
        headers=admin_header, 
        json=temp_user_data.model_dump()
    )
    assert create_response.status_code == 200, (
        f"创建临时用户失败: {create_response.text}"
    )

    temp_user_id = create_response.json()["id"]

    # 现在升级这个临时用户
    upgrade_response = await async_client.post(
        "/user/upgrade_level", 
        headers=admin_header, 
        json={"user_id": temp_user_id, "new_level": UserLevel.ADMIN}
    )
    assert upgrade_response.status_code == 200, (
        f"/user/upgrade_level 升级失败: {upgrade_response.text}"
    )


