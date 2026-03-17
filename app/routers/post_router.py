from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from ..service import PostService
from ..schemas.post_schemas import (
    PostCreate,
    PostUpdate,
    PostBrief,
    PostDetail,
    PostSearch,
)
from ..core import get_current_user, require_admin
from ..models import User

router = APIRouter(prefix="/post", tags=["post"])


# 依赖项
async def view_add(post_id: int, request: Request, response: Response) -> None:
    """浏览量 +1，用 Cookie 做 1 小时去重"""
    cookie_key = f"post_viewed_{post_id}"
    if request.cookies.get(cookie_key):
        return

    response.set_cookie(key=cookie_key, value="1", max_age=3600, httponly=True)
    await PostService.increment_view_count(post_id)


# 路由
@router.post("/create", response_model=PostDetail, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """创建文章（需登录）"""
    post = await PostService.create_post(data, author_id=current_user.id)
    return post

@router.get("/search", response_model=list[PostBrief])
async def search_posts(
    search: Annotated[PostSearch, Depends()],
):
    """按条件搜索文章列表（公开）"""
    return await PostService.search_posts(search)


@router.get("/id/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: int, # 给view_add用的参数，后同 
    _: Annotated[None, Depends(view_add)],
):
    """获取文章详情，自动增加浏览量（公开）"""
    return await PostService.get_post_by_id(post_id)


@router.get("/slug/{slug}", response_model=PostDetail)
async def get_post_by_slug(
    slug: str,
    request: Request,
    response: Response,
):
    """通过 slug 获取文章详情（公开）"""
    post = await PostService.get_post_by_slug(slug)
    await view_add(post.id, request, response)
    return post


@router.post("/update/{post_id}", response_model=PostDetail)
async def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: Annotated[User, Depends(require_admin)],
):
    """更新文章（需管理员）"""
    return await PostService.update_post(post_id, data)


@router.post("/delete/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: Annotated[User, Depends(require_admin)],
):
    """删除文章（需管理员）"""
    await PostService.delete_post(post_id)