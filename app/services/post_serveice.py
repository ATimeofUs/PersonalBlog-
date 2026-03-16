from ..models import Post, PostStatus, Category, User, ServiceError
from ..schemas.post_schemas import PostCreate, PostUpdate, PostSearch
from datetime import datetime, timezone
from tortoise.expressions import Q

class PostService:
    """
    文章业务层类
    
    所有方法均为静态方法（@staticmethod），负责处理 Post 模型的增删改查及业务校验。
    """

    @staticmethod
    async def create_post(data: PostCreate, author_id: int) -> Post:
        """创建新文章并持久化到数据库"""
        try:
            # 若没有提供 slug，用 title 简单生成（router 层也可以预处理）
            slug = data.slug or data.title.replace(" ", "-").lower()

            create_kwargs = dict(
                title=data.title,
                slug=slug,
                excerpt=data.excerpt,
                content=data.content,
                status=data.status,
                is_featured=data.is_featured,
                author_id=author_id,
            )

            if data.category_id is not None:
                # 验证分类是否存在
                if not await Category.filter(id=data.category_id).exists():
                    raise ServiceError("分类不存在", code="NOT_FOUND", status_code=404)
                create_kwargs["category_id"] = data.category_id

            # 发布状态时自动设置发布时间
            if data.status == PostStatus.PUBLISHED:
                create_kwargs["published_at"] = datetime.now(timezone.utc)

            new_post = await Post.create(**create_kwargs)
            return new_post

        except ServiceError:
            raise
        except Exception:
            raise ServiceError("文章标题或别名已存在", code="CONFLICT", status_code=409)

    @staticmethod
    async def get_post_by_id(post_id: int) -> Post:
        """通过主键 ID 精确查找文章，同时预取 author 与 category"""
        post = (
            await Post.filter(id=post_id)
            .prefetch_related("author", "category")
            .first()
        )
        if not post:
            raise ServiceError("文章不存在", code="NOT_FOUND", status_code=404)
        return post

    @staticmethod
    async def get_post_by_slug(slug: str) -> Post:
        """通过 slug 精确查找文章，同时预取 author 与 category"""
        post = (
            await Post.filter(slug=slug)
            .prefetch_related("author", "category")
            .first()
        )
        if not post:
            raise ServiceError("文章不存在", code="NOT_FOUND", status_code=404)
        return post


    @staticmethod
    async def update_post(post_id: int, data: PostUpdate) -> Post:
        """更新现有文章的内容和属性（PATCH 语义，仅更新非 None 字段）"""
        post = await PostService.get_post_by_id(post_id)

        update_data = data.model_dump(exclude_none=True)

        # 分类校验
        if "category_id" in update_data:
            if update_data["category_id"] is not None:
                if not await Category.filter(id=update_data["category_id"]).exists():
                    raise ServiceError("分类不存在", code="NOT_FOUND", status_code=404)

        # 首次从草稿变为发布时，自动补全 published_at
        if (
            "status" in update_data
            and update_data["status"] == PostStatus.PUBLISHED
            and post.status != PostStatus.PUBLISHED
            and "published_at" not in update_data
        ):
            update_data["published_at"] = datetime.now(timezone.utc)

        try:
            await post.update_from_dict(update_data).save()
        except Exception:
            raise ServiceError("更新失败，slug 可能已被占用", code="CONFLICT", status_code=409)

        # 重新预取关联对象，确保返回数据完整
        await post.fetch_related("author", "category")
        return post

    @staticmethod
    async def increment_view_count(post_id: int) -> None:
        """原子性地将指定文章的浏览次数 +1"""
        post = await Post.filter(id=post_id).first()
        if not post:
            raise ServiceError("文章不存在", code="NOT_FOUND", status_code=404)
        
        post.view_count += 1
        await post.save(update_fields=["view_count"])
        
    @staticmethod
    async def delete_post(post_id: int) -> None:
        """删除指定文章"""
        post = await Post.filter(id=post_id).first()
        if not post:
            raise ServiceError("文章不存在", code="NOT_FOUND", status_code=404)
        await post.delete()
        
    @staticmethod
    async def search_posts(search: PostSearch) -> list[Post]:
        """根据搜索条件查询文章列表，支持分页"""
        query = Post.all()

        if search.keyword:
            query = query.filter(
                Q(title__icontains=search.keyword) | Q(content__icontains=search.keyword)
            )
        if search.category_id is not None:
            query = query.filter(category_id=search.category_id)
        if search.author_id is not None:
            query = query.filter(author_id=search.author_id)
        if search.status is not None:
            query = query.filter(status=search.status)
        if search.is_featured is not None:
            query = query.filter(is_featured=search.is_featured)

        return await query.prefetch_related("author", "category").offset(search.offset).limit(search.limit)
        
