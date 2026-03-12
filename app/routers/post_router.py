from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..services import PostService
from ..schemas.pydantic_model import PostCreate, PostUpdate, PostOut, PostBrief, PostQuery
from ..core import get_current_user, require_admin
from ..schemas.pydantic_model import UserOut

router = APIRouter(prefix="/post", tags=["post"])


# ── 1. 公开查询接口（无需登录）────────────────────────────────────────────────

@router.get("/detail/{post_id}", response_model=PostOut)
async def get_post_by_id(post_id: int):
    """按 ID 获取文章详情，同时增加浏览量"""
    try:
        post = await PostService.get_post_by_id(post_id)
        return post
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc[:15]))


@router.get("/slug/{slug}", response_model=PostOut)
async def get_post_by_slug(slug: str):
    """按 slug 获取文章详情（前端 URL 路由常用），同时增加浏览量"""
    try:
        post = await PostService.get_post_by_slug(slug)
        return post
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc[:15]))


@router.post("/list", response_model=List[PostBrief])
async def get_posts(query: PostQuery):
    """通用文章列表查询：支持关键词、分类、状态、作者过滤，统一分页
    使用 POST 传递 query 对象，避免复杂查询参数拼在 URL 上
    """
    try:
        return await PostService.get_posts(query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


# ── 2. 需要登录的接口 ──────────────────────────────────────────────────────────

@router.get("/my", response_model=List[PostBrief])
async def get_my_posts(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    status: Annotated[int | None, Query(ge=0, le=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """获取当前登录用户自己的文章列表，author_id 由后端注入"""
    query = PostQuery(
        keyword=keyword,
        category_id=category_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    try:
        return await PostService.get_posts_by_user(user=current_user, query=query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


@router.post("/create", response_model=PostOut)
async def create_post(
    data: Annotated[PostCreate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """创建文章，author_id 由后端强制注入"""
    try:
        return await PostService.create_post(data=data, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


@router.post("/update/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    data: Annotated[PostUpdate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """更新文章，只有作者或管理员可操作"""
    try:
        return await PostService.update_post(post_id=post_id, data=data, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


@router.post("/delete/{post_id}", response_model=bool)
async def delete_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """删除文章，只有作者或管理员可操作"""
    try:
        return await PostService.delete_post(post_id=post_id, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


# ── 3. 状态切换接口 ────────────────────────────────────────────────────────────

@router.post("/publish/{post_id}", response_model=PostOut)
async def publish_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """发布文章（已发布则直接返回）"""
    try:
        return await PostService.publish_post(post_id=post_id, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


@router.post("/unpublish/{post_id}", response_model=PostOut)
async def unpublish_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """撤回文章为草稿"""
    try:
        return await PostService.unpublish_post(post_id=post_id, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc[:15]))


@router.post("/featured/{post_id}", response_model=PostOut)
async def toggle_featured(
    post_id: int,
    current_user: Annotated[UserOut, Depends(require_admin)],
):
    """置顶/取消置顶，仅管理员"""
    try:
        return await PostService.toggle_featured(post_id=post_id, user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc[:15]))
    