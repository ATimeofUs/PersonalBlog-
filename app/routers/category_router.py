from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..services import CategoryService
from ..schemas.pydantic_model import CategoryCreate, CategoryUpdate, CategoryOut, CategoryBrief, PostBrief
from ..schemas.pydantic_model import UserOut
from ..core import require_admin

router = APIRouter(prefix="/category", tags=["category"])


# ── 1. 公开查询接口（无需登录）────────────────────────────────────────────────

@router.get("/detail/{cate_id}", response_model=CategoryOut)
async def get_category_by_id(cate_id: int):
    """按 ID 获取分类详情"""
    try:
        return await CategoryService.get_category_by_id(cate_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/list", response_model=List[CategoryOut])
async def get_categories_list(
    name: Annotated[str, Query(max_length=50)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """获取分类列表，支持按名称模糊搜索，name 为空时返回全部"""
    try:
        return await CategoryService.get_categories_list(
            cate_name=name, limit=limit, offset=offset
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{cate_id}/posts", response_model=List[PostBrief])
async def get_category_posts(
    cate_id: int,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """获取指定分类下已发布的文章列表"""
    try:
        return await CategoryService.get_category_posts(
            cate_id=cate_id, limit=limit, offset=offset
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── 2. 管理员接口 ──────────────────────────────────────────────────────────────

@router.post("/create", response_model=CategoryOut)
async def create_category(
    data: Annotated[CategoryCreate, Body(...)],
    current_user: Annotated[UserOut, Depends(require_admin)],
):
    """创建分类，仅管理员"""
    try:
        return await CategoryService.create_category(cate=data, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/update/{cate_id}", response_model=CategoryOut)
async def update_category(
    cate_id: int,
    data: Annotated[CategoryUpdate, Body(...)],
    current_user: Annotated[UserOut, Depends(require_admin)],
):
    """更新分类，仅管理员"""
    try:
        return await CategoryService.update_category(
            cate_id=cate_id, cate=data, user=current_user
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/delete/{cate_id}", response_model=bool)
async def delete_category(
    cate_id: int,
    current_user: Annotated[UserOut, Depends(require_admin)],
):
    """删除分类，仅管理员"""
    try:
        return await CategoryService.delete_category(cate_id=cate_id, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))