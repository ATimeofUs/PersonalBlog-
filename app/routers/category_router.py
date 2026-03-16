"""
GET     /category/list
GET     /category/detail/{category_id}
GET     /category/slug/{slug}
POST    /category/create
POST    /category/update/{category_id}
POST    /category/delete/{category_id}
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from ..core import require_admin
from ..models import ServiceError
from ..schemas.category_schemas import (
	CategoryBrief,
	CategoryCreate,
	CategoryDetail,
	CategoryUpdate,
    CategorySearch
)
from ..schemas.user_schemas import UserData
from ..services.categroy_serveice import CategoryService

router = APIRouter(prefix="/category", tags=["category"])


def _raise_service_error(exc: ServiceError) -> None:
	raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.get("/list", response_model=list[CategoryBrief])
async def list_categories(search: CategorySearch = Depends()) -> list[CategoryBrief]:
	"""获取分类列表（公开）"""
	try:
		return await CategoryService.list_categories(limit=search.limit, offset=search.offset)
	except ServiceError as exc:
		_raise_service_error(exc)


@router.get("/detail/{category_id}", response_model=CategoryDetail)
async def get_category_detail(category_id: int) -> CategoryDetail:
	"""按 ID 获取分类详情（公开）"""
	try:
		return await CategoryService.get_category_by_id(category_id=category_id)
	except ServiceError as exc:
		_raise_service_error(exc)


@router.get("/slug/{slug}", response_model=CategoryDetail)
async def get_category_by_slug(slug: str) -> CategoryDetail:
	"""按 slug 获取分类详情（公开）"""
	try:
		return await CategoryService.get_category_by_slug(slug=slug)
	except ServiceError as exc:
		_raise_service_error(exc)


@router.post("/create", response_model=CategoryDetail)
async def create_category(
	data: Annotated[CategoryCreate, Body(...)],
	current_user: Annotated[UserData, Depends(require_admin)],
) -> CategoryDetail:
	"""创建分类（管理员）"""
	try:
		return await CategoryService.create_category(data=data)
	except ServiceError as exc:
		_raise_service_error(exc)


@router.post("/update/{category_id}", response_model=CategoryDetail)
async def update_category(
	category_id: int,
	data: Annotated[CategoryUpdate, Body(...)],
	current_user: Annotated[UserData, Depends(require_admin)],
) -> CategoryDetail:
	"""更新分类（管理员）"""
	try:
		return await CategoryService.update_category(category_id=category_id, data=data)
	except ServiceError as exc:
		_raise_service_error(exc)


@router.post("/delete/{category_id}", response_model=bool)
async def delete_category(
	category_id: int,
	current_user: Annotated[UserData, Depends(require_admin)],
) -> bool:
	"""删除分类（管理员）"""
	try:
		return await CategoryService.delete_category(category_id=category_id)
	except ServiceError as exc:
		_raise_service_error(exc)
