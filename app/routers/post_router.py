from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response
from datetime import datetime, timedelta

from ..services import PostService
from ..models import ServiceError
from ..schemas.pydantic_model import (
    PostCreate,
    PostUpdate,
    PostOut,
    PostBrief,
    PostQuery,
)
from ..core import get_current_user, require_admin
from ..schemas.pydantic_model import UserOut

router = APIRouter(prefix="/post", tags=["post"])


# ── 1. 公开查询接口（无需登录）────────────────────────────────────────────────

SPAN_TIME = timedelta(seconds=600)


async def view_times_add(
    request: Request,
    response: Response,
    post_id: int | None = None,
    slug: str | None = None,
) -> None:
    if post_id is None and slug is not None:
        try:
            post = await PostService.get_post_by_slug(slug)
            post_id = post.id
        except ServiceError:
            # slug 不存在时由路由主逻辑统一返回错误
            return

    if post_id is None:
        return

    c_key = f"post_{post_id}"
    lst = request.cookies.get(c_key)

    if lst is None:
        lst = datetime.min
    else:
        try:
            lst = datetime.fromisoformat(lst)
        except ValueError:
            lst = datetime.min

    if datetime.now() - lst > SPAN_TIME:
        await PostService.increment_view_count(post_id)

        response.set_cookie(
            key=c_key,
            value=datetime.now().isoformat(),
            max_age=3600 * 24 * 60,
            httponly=True,
        )


def _raise_http_from_service_error(exc: ServiceError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.get("/detail/{post_id}", response_model=PostOut)
async def get_post_by_id(
    post_id: int, _: None = Depends(view_times_add)
):
    """按 ID 获取文章详情，同时增加浏览量"""
    try:
        post = await PostService.get_post_by_id(post_id)
        return post
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="获取文章详情失败")


@router.get("/slug/{slug}", response_model=PostOut)
async def get_post_by_slug(slug: str,  _: None = Depends(view_times_add)):
    """按 slug 获取文章详情（前端 URL 路由常用），同时增加浏览量"""
    try:
        post = await PostService.get_post_by_slug(slug)
        return post
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="获取文章详情失败")


@router.post("/list", response_model=List[PostBrief])
async def get_posts(query: PostQuery):
    """通用文章列表查询：支持关键词、分类、状态、作者过滤，统一分页
    使用 POST 传递 query 对象，避免复杂查询参数拼在 URL 上
    """
    try:
        return await PostService.get_posts(query)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="获取文章列表失败")


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
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="获取个人文章失败")


@router.post("/create", response_model=PostOut)
async def create_post(
    data: Annotated[PostCreate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """创建文章，author_id 由后端强制注入"""
    try:
        return await PostService.create_post(data=data, user=current_user)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="创建文章失败")


@router.post("/update/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    data: Annotated[PostUpdate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """更新文章，只有作者或管理员可操作"""
    try:
        return await PostService.update_post(
            post_id=post_id, data=data, user=current_user
        )
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="更新文章失败")


@router.post("/delete/{post_id}", response_model=bool)
async def delete_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """删除文章，只有作者或管理员可操作"""
    try:
        return await PostService.delete_post(post_id=post_id, user=current_user)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="删除文章失败")


# ── 3. 状态切换接口 ────────────────────────────────────────────────────────────


@router.post("/publish/{post_id}", response_model=PostOut)
async def publish_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """发布文章（已发布则直接返回）"""
    try:
        return await PostService.publish_post(post_id=post_id, user=current_user)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="发布文章失败")


@router.post("/unpublish/{post_id}", response_model=PostOut)
async def unpublish_post(
    post_id: int,
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    """撤回文章为草稿"""
    try:
        return await PostService.unpublish_post(post_id=post_id, user=current_user)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="撤回文章失败")


@router.post("/featured/{post_id}", response_model=PostOut)
async def toggle_featured(
    post_id: int,
    current_user: Annotated[UserOut, Depends(require_admin)],
):
    """置顶/取消置顶，仅管理员"""
    try:
        return await PostService.toggle_featured(post_id=post_id, user=current_user)
    except ServiceError as exc:
        _raise_http_from_service_error(exc)
    except Exception:
        raise HTTPException(status_code=500, detail="切换置顶状态失败")
