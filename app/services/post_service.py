from datetime import datetime, timezone
from typing import List

from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.expressions import Q

from ..models import (
    Post,
    PostStatus,
    UserLevel,
    PostNotFoundError,
    DuplicateSlugError,
    PermissionDeniedError,
)
from ..schemas import PostCreate, PostUpdate, UserOut, PostQuery


# ── 权限检查 ──────────────────────────────────────────────────────────────────

def _is_admin(user: UserOut) -> bool:
    return user.level >= UserLevel.ADMIN


async def _require_post_owner_or_admin(post: Post, user: UserOut) -> None:
    """不是作者也不是管理员时抛出 ServiceError"""
    if post.author_id != user.id and not _is_admin(user):
        raise PermissionDeniedError(action="modify", resource="post")


# ── PostService ───────────────────────────────────────────────────────────────

class PostService:
    # ── 查询 ──────────────────────────────────────────────────────────────────
    @staticmethod
    async def get_post_by_id(post_id: int) -> Post:
        """按 ID 取单篇文章，不存在时抛出 ServiceError"""
        try:
            # select_related 预加载关联表，避免 N+1
            return await Post.get(id=post_id).select_related("author", "category")
        except DoesNotExist:
            raise PostNotFoundError(post_id=post_id)

    @staticmethod
    async def get_post_by_slug(slug: str) -> Post:
        """按 slug 取单篇文章（前端 URL 路由常用）"""
        try:
            return await Post.get(slug=slug).select_related("author", "category")
        except DoesNotExist:
            raise PostNotFoundError(slug=slug)

    @staticmethod
    async def get_posts(query: PostQuery) -> List[Post]:
        """通用列表查询：支持关键词搜索、分类、状态、作者过滤，统一分页"""
        qs = Post.all().select_related("author", "category")

        if query.keyword:
            qs = qs.filter(
                Q(title__icontains=query.keyword) | Q(excerpt__icontains=query.keyword)
            )
        if query.category_id is not None:
            qs = qs.filter(category_id=query.category_id)
        if query.status is not None:
            qs = qs.filter(status=query.status)
        if query.author_id is not None:
            qs = qs.filter(author_id=query.author_id)

        return await qs.order_by("-created_at").limit(query.limit).offset(query.offset)

    @staticmethod
    async def get_posts_by_user(user: UserOut, query: PostQuery) -> List[Post]:
        """获取某用户自己的文章，强制绑定 author_id，不允许外部覆盖"""
        bound_query = query.model_copy(update={"author_id": user.id})
        return await PostService.get_posts(bound_query)

    # ── 写操作 ────────────────────────────────────────────────────────────────

    @staticmethod
    async def create_post(data: PostCreate, user: UserOut) -> Post:
        """创建文章，author_id 由 user 注入，忽略前端传入的 author_id"""
        try:
            post = await Post.create(
                title=data.title,
                slug=data.slug,
                excerpt=data.excerpt,
                content=data.content,
                status=data.status,
                is_featured=data.is_featured,
                category_id=data.category_id,
                author_id=user.id,          
                view_count=0,
            )
            return await Post.get(id=post.id).select_related("author", "category")
        except IntegrityError:
            raise DuplicateSlugError(slug=data.slug)

    @staticmethod
    async def update_post(post_id: int, data: PostUpdate, user: UserOut) -> Post:
        """更新文章，只有作者或管理员可操作"""
        post = await PostService.get_post_by_id(post_id)
        await _require_post_owner_or_admin(post, user)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return post

        # 如果状态从非发布改为发布，补充 published_at
        if update_data.get("status") == PostStatus.PUBLISHED and post.status != PostStatus.PUBLISHED:
            update_data["published_at"] = datetime.now(timezone.utc)

        try:
            for key, value in update_data.items():
                setattr(post, key, value)
            post.updated_at = datetime.now(timezone.utc)
            await post.save()
            return post
        except IntegrityError:
            raise DuplicateSlugError(slug=update_data.get("slug"))

    @staticmethod
    async def delete_post(post_id: int, user: UserOut) -> bool:
        """删除文章，只有作者或管理员可操作"""
        post = await PostService.get_post_by_id(post_id)
        await _require_post_owner_or_admin(post, user)
        await post.delete()
        return True

    # ── 状态切换（语义明确，router 层权限好控制）─────────────────────────────

    @staticmethod
    async def publish_post(post_id: int, user: UserOut) -> Post:
        """发布文章"""
        post = await PostService.get_post_by_id(post_id)
        await _require_post_owner_or_admin(post, user)

        if post.status == PostStatus.PUBLISHED:
            return post  # 幂等，已发布直接返回

        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.now(timezone.utc)
        post.updated_at = datetime.now(timezone.utc)
        await post.save()
        return post

    @staticmethod
    async def unpublish_post(post_id: int, user: UserOut) -> Post:
        """撤回为草稿"""
        post = await PostService.get_post_by_id(post_id)
        await _require_post_owner_or_admin(post, user)

        post.status = PostStatus.DRAFT
        post.updated_at = datetime.now(timezone.utc)
        await post.save()
        return post

    @staticmethod
    async def toggle_featured(post_id: int, user: UserOut) -> Post:
        """置顶/取消置顶，仅管理员"""
        if not _is_admin(user):
            raise PermissionDeniedError(action="feature", resource="post")
        post = await PostService.get_post_by_id(post_id)
        post.is_featured = not post.is_featured
        post.updated_at = datetime.now(timezone.utc)
        await post.save()
        return post

    # ── 辅助 ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def increment_view_count(post_id: int) -> None:
        """浏览量 +1，使用数据库原子更新避免并发问题"""
        await Post.filter(id=post_id).update(view_count=Post.view_count + 1)