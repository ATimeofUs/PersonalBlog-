import logging

import pytest

from app.schemas import CategoryCreate, CategorySearch, CategoryUpdate

pytestmark = pytest.mark.asyncio

CATEGORY_DB_ID = None
CATEGORY_SLUG = "test-category"


@pytest.fixture(autouse=True)
def init_log(get_log_file):
	log_file = get_log_file("test_category")
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


# POST /category/create - Create new category (admin only)
async def test_category_create(async_client, admin_header):
	category_create = CategoryCreate(
		name="测试分类",
		slug=CATEGORY_SLUG,
		description="这是测试分类的描述",
	)

	response = await async_client.post(
		"/category/create",
		headers=admin_header,
		json=category_create.model_dump(),
	)

	assert response.status_code // 100 == 2, f"/category/create 创建失败: {response.text}"
	data = response.json()
	assert data["name"] == category_create.name
	assert data["slug"] == category_create.slug
	logging.info("/category/create 测试通过，返回数据：%s", data)

	global CATEGORY_DB_ID
	CATEGORY_DB_ID = data["id"]


# GET /category/list - List categories with optional limit/offset (via CategorySearch) - public
async def test_category_list(async_client):
	search_data = CategorySearch(limit=10, offset=0)
	response = await async_client.get(
		"/category/list",
		params=search_data.model_dump(),
	)

	assert response.status_code // 100 == 2, f"/category/list 获取失败: {response.text}"
	data = response.json()
	assert isinstance(data, list), "返回数据应为分类列表"
	logging.info("/category/list 测试通过，返回数据：%s", data)


# GET /category/detail/{category_id} - Get category by ID - public
async def test_category_detail(async_client):
	global CATEGORY_DB_ID
	category_id = CATEGORY_DB_ID
	assert category_id is not None, "CATEGORY_DB_ID 未设置，无法进行详情测试"

	response = await async_client.get(f"/category/detail/{category_id}")
	assert response.status_code // 100 == 2, f"/category/detail 获取失败: {response.text}"

	data = response.json()
	assert data["id"] == category_id
	logging.info("/category/detail 测试通过，返回数据：%s", data)


# GET /category/slug/{slug} - Get category by slug - public
async def test_category_slug(async_client):
	response = await async_client.get(f"/category/slug/{CATEGORY_SLUG}")
	assert response.status_code // 100 == 2, f"/category/slug 获取失败: {response.text}"

	data = response.json()
	assert data["slug"] == CATEGORY_SLUG
	logging.info("/category/slug 测试通过，返回数据：%s", data)


# POST /category/update/{category_id} - Update existing category (admin only)
async def test_category_update(async_client, admin_header):
	global CATEGORY_DB_ID
	category_id = CATEGORY_DB_ID
	assert category_id is not None, "CATEGORY_DB_ID 未设置，无法进行更新测试"

	update_data = CategoryUpdate(
		name="测试分类-更新",
		slug="test-category-updated",
		description="这是更新后的测试分类描述",
	)

	response = await async_client.post(
		f"/category/update/{category_id}",
		headers=admin_header,
		json=update_data.model_dump(exclude_none=True),
	)
	assert response.status_code // 100 == 2, f"/category/update 更新失败: {response.text}"

	data = response.json()
	assert data["name"] == update_data.name
	assert data["slug"] == update_data.slug
	assert data["description"] == update_data.description
	logging.info("/category/update 测试通过，返回数据：%s", data)


# POST /category/delete/{category_id} - Delete category (admin only)
async def test_category_delete(async_client, admin_header):
	global CATEGORY_DB_ID
	category_id = CATEGORY_DB_ID
	assert category_id is not None, "CATEGORY_DB_ID 未设置，无法进行删除测试"

	response = await async_client.post(
		f"/category/delete/{category_id}",
		headers=admin_header,
	)
	assert response.status_code // 100 == 2, f"/category/delete 删除失败: {response.text}"
	logging.info("/category/delete 测试通过，分类 ID: %s 已删除", category_id)