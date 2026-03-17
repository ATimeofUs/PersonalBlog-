from tortoise.exceptions import IntegrityError

from ..models import Category, ServiceError
from ..schemas.category_schemas import CategoryCreate, CategoryUpdate


class CategoryCache:
    """数据库类，负责 Category 模型的增删改查。"""

    @staticmethod
    async def create_category(data: CategoryCreate) -> Category:
        """创建分类"""
        pass

    @staticmethod
    async def get_category_by_id(category_id: int) -> Category:
        """按 ID 获取分类"""
        pass

    @staticmethod
    async def get_category_by_slug(slug: str) -> Category:
        """按 slug 获取分类"""
        pass

    @staticmethod
    async def update_category(category_id: int, data: CategoryUpdate) -> Category:
        """更新分类（仅更新非 None 字段）"""
        pass

    @staticmethod
    async def delete_category(category_id: int) -> bool:
        """删除分类"""
        pass

    @staticmethod
    async def list_categories(limit: int = 20, offset: int = 0) -> list[Category]:
        """获取分类列表"""
        pass