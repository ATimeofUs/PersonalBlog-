import pytest
import logging

# my code
from .conftest import ADMIN_USER

from app.schemas import (
    PostUpdate,
    PostStatus,
    PostBrief,
    PostCreate,
    PostDetail,
    PostSearch,
    CategoryCreate,
    CategoryUpdate,
    CategoryBrief,
    CategoryDetail,
    CategorySearch,
)

from app.models import User, UserLevel


pytestmark = pytest.mark.asyncio

POST_DB_ID = None


@pytest.fixture(autouse=True)
def init_log(get_log_file):
    log_file = get_log_file("test_post")
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


# 文章模块接口列表：
# POST    /post                创建文章（需登录）                 请求体 PostCreate，返回 PostDetail
async def test_post_create(async_client, admin_header):
    category_create = CategoryCreate(
        name="测试分类", 
        slug="test-category", 
        description="这是测试分类的描述"
    )

    # POST /category/create - Create new category (admin only)

    logging.info("category_create.model_dump(): %s", category_create.model_dump())

    response = await async_client.post(
        "/category/create", headers=admin_header, json=category_create.model_dump()
    )

    logging.info(
        "/category/create 响应状态码: %s, 响应内容: %s",
        response.status_code,
        response.text,
    )
    assert response.status_code // 100 == 2, f"/category 创建失败: {response.text}"

    new_category_id = response.json()["id"]

    post_create_data = PostCreate(
        title="测试文章",
        content="这是测试文章的内容",
        slug="test-post",
        excerpt="这是测试文章的摘要",
        is_featured=False,
        status=PostStatus.DRAFT,
        category_id=new_category_id,
    )

    response = await async_client.post(
        "/post/create", headers=admin_header, json=post_create_data.model_dump()
    )
    assert response.status_code // 100 == 2, f"/post 创建失败: {response.text}"
    logging.info(
        "/post/create 响应状态码: %s, 响应内容: %s", response.status_code, response.text
    )

    data = response.json()
    assert data["title"] == post_create_data.title
    assert data["content"] == post_create_data.content
    logging.info("/post 创建测试通过，返回数据：%s", data)

    global POST_DB_ID
    POST_DB_ID = data["id"]


# GET     /post/search         搜索文章列表（公开）               查询参数 PostSearch，返回 list[PostBrief]
async def test_post_search(async_client):
    post_search_data = PostSearch(
        keyword="测试",
        status=PostStatus.PUBLISHED,
        offset=1,
        limit=10,
    )

    # exclude_none=True 只传非 None 的参数，避免发送 status=None 导致搜索失败
    response = await async_client.get("/post/search", params=post_search_data.model_dump(exclude_none=True)) 

    assert response.status_code // 100 == 2, f"/post/search 获取失败: {response.text}"

    data = response.json()
    assert isinstance(data, list), "返回数据应为文章列表"
    logging.info("/post/search 测试通过，返回数据：%s", data)


# GET     /post/{post_id}      获取文章详情（公开，自动加浏览量）  路径参数 post_id，返回 PostDetail
# TODO : pass this


# GET     /post/slug/{slug}    通过 slug 获取文章详情（公开）      路径参数 slug，返回 PostDetail
async def test_post_slug(async_client, admin_header):
    slug = "test-post"

    response = await async_client.get(f"/post/slug/{slug}", headers=admin_header)
    assert response.status_code // 100 == 2, f"/post/slug 获取失败: {response.text}"


# POST    /post/update/{post_id} 更新文章（需管理员）              路径参数 post_id，请求体 PostUpdate，返回 PostDetail
async def test_post_update(async_client, admin_header):
    global POST_DB_ID
    post_id = POST_DB_ID
    assert post_id is not None, "POST_DB_ID 未设置，无法进行更新测试"

    post_update_data = PostUpdate(
        title="测试文章 - 更新",
        content="这是测试文章更新后的内容",
        excerpt="这是测试文章更新后的摘要",
        is_featured=True,
        status=PostStatus.PUBLISHED,
    )

    response = await async_client.post(
        f"/post/update/{post_id}",
        headers=admin_header,
        json=post_update_data.model_dump(),
    )
    assert response.status_code // 100 == 2, f"/post/update 更新失败: {response.text}"
    data = response.json()
    assert data["title"] == post_update_data.title
    assert data["content"] == post_update_data.content
    assert data["is_featured"] == post_update_data.is_featured
    assert data["status"] == post_update_data.status
    logging.info("/post/update 测试通过，返回数据：%s", data)


# POST    /post/delete/{post_id} 删除文章（需管理员）              路径参数 post_id，返回 204 No Content
async def test_post_delete(async_client, admin_header):
    global POST_DB_ID
    post_id = POST_DB_ID
    assert post_id is not None, "POST_DB_ID 未设置，无法进行删除测试"

    response = await async_client.post(
        f"/post/delete/{post_id}",
        headers=admin_header,
    )
    assert response.status_code // 100 == 2, f"/post/delete 删除失败: {response.text}"
    logging.info("/post/delete 测试通过，文章 ID: %s 已删除", post_id)
