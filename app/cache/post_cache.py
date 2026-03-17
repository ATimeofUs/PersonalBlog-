from ..models import Post, PostStatus, Category, User, ServiceError
from ..schemas.post_schemas import PostCreate, PostUpdate, PostSearch
from datetime import datetime, timezone
from tortoise.expressions import Q

class PostCache:
    """
    文章数据库类
    所有方法均为静态方法（@staticmethod），负责处理 Post 模型的增删改查及业务校验。
    """

    @staticmethod
    async def create_post(data: PostCreate, author_id: int) -> Post:
        """创建新文章并持久化到数据库"""
        pass

    @staticmethod
    async def get_post_by_id(post_id: int) -> Post:
        """通过主键 ID 精确查找文章，同时预取 author 与 category"""
        pass

    @staticmethod
    async def get_post_by_slug(slug: str) -> Post:
        """通过 slug 精确查找文章，同时预取 author 与 category"""
        pass

    @staticmethod
    async def update_post(post_id: int, data: PostUpdate) -> Post:
        """更新现有文章的内容和属性（PATCH 语义，仅更新非 None 字段）"""
        pass

    @staticmethod
    async def increment_view_count(post_id: int) -> None:
        """原子性地将指定文章的浏览次数 +1"""
        pass

    @staticmethod
    async def delete_post(post_id: int) -> None:
        """删除指定文章"""
        pass

    @staticmethod
    async def search_posts(search: PostSearch) -> list[Post]:
        """根据搜索条件查询文章列表，支持分页"""
        pass