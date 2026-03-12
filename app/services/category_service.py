from datetime import datetime, timezone
from typing import List

from tortoise.exceptions import DoesNotExist, IntegrityError

from ..models import Category, Post, PostStatus, ServiceError, UserLevel
from ..schemas import CategoryCreate, CategoryOut, CategoryUpdate
from ..schemas import UserOut, PostBrief


def _is_admin(user: UserOut) -> bool:
    return user.level >= UserLevel.ADMIN


class CategoryService:
    @staticmethod
    async def create_category(cate: CategoryCreate, user: UserOut) -> Category:
        if not _is_admin(user):
            raise ServiceError("无权创建分类")
        try:
            category = await Category.create(
                name=cate.name,
                slug=cate.slug,
                description=cate.description,
            )
            return category
        except IntegrityError:
            raise ServiceError("分类名称或 slug 已存在")

    @staticmethod
    async def get_category_by_id(cate_id: int) -> Category:
        try:
            return await Category.get(id=cate_id)
        except DoesNotExist:
            raise ServiceError("分类不存在")

    @staticmethod
    async def get_category_by_name(name: str) -> Category:
        try:
            return await Category.get(name=name)
        except DoesNotExist:
            raise ServiceError("分类不存在")

    @staticmethod
    async def get_categories_list(
        cate_name: str = "", limit: int = 20, offset: int = 0
    ) -> List[Category]:
        """获取分类列表，cate_name 为空时返回全部"""
        
        # TODO: 这里没有具体的性能优化措施
        qs = Category.all()
        if cate_name:
            qs = qs.filter(name__icontains=cate_name)
        return await qs.limit(limit).offset(offset)

    @staticmethod
    async def update_category(
        cate_id: int, cate: CategoryUpdate, user: UserOut
    ) -> Category:
        if not _is_admin(user):
            raise ServiceError("无权修改分类")

        try:
            category = await Category.get(id=cate_id)
        except DoesNotExist:
            raise ServiceError("分类不存在")

        # 只更新前端实际传入的字段，避免 None 覆盖已有数据
        update_data = cate.model_dump(exclude_unset=True)
        if not update_data:
            return category

        try:
            for key, value in update_data.items():
                setattr(category, key, value)
            await category.save()
            return category
        except IntegrityError:
            raise ServiceError("分类名称或 slug 已存在")

    @staticmethod
    async def delete_category(cate_id: int, user: UserOut) -> None:
        if not _is_admin(user):
            raise ServiceError("无权删除分类")
        try:
            category = await Category.get(id=cate_id)
            await category.delete()
        except DoesNotExist:
            raise ServiceError("分类不存在")

    @staticmethod
    async def get_category_posts(
        cate_id: int, limit: int = 20, offset: int = 0
    ) -> List[PostBrief]:
        """获取指定分类下已发布的文章列表，分类不存在时抛出 ServiceError"""
        # 先确认分类存在，不存在直接抛错
        if not await Category.filter(id=cate_id).exists():
            raise ServiceError("分类不存在")

        posts = (
            await Post.filter(category_id=cate_id, status=PostStatus.PUBLISHED)
            .select_related("author", "category")
            .limit(limit)
            .offset(offset)
        )
        return [PostBrief.model_validate(post) for post in posts]
