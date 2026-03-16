from tortoise.exceptions import IntegrityError

from ..models import Category, ServiceError
from ..schemas.category_schemas import CategoryCreate, CategoryUpdate


class CategoryService:
	"""分类业务层类，负责 Category 模型的增删改查。"""

	@staticmethod
	async def create_category(data: CategoryCreate) -> Category:
		"""创建分类"""

		try:
			return await Category.create(
				name=data.name,
				slug=data.slug,
				description=data.description,
			)
		except IntegrityError:
			raise ServiceError("分类名称或别名已存在", code="CONFLICT", status_code=409)

	@staticmethod
	async def get_category_by_id(category_id: int) -> Category:
		"""按 ID 获取分类"""
		category = await Category.filter(id=category_id).first()
		if not category:
			raise ServiceError("分类不存在", code="NOT_FOUND", status_code=404)
		return category

	@staticmethod
	async def get_category_by_slug(slug: str) -> Category:
		"""按 slug 获取分类"""
		category = await Category.filter(slug=slug).first()
		if not category:
			raise ServiceError("分类不存在", code="NOT_FOUND", status_code=404)
		return category

	@staticmethod
	async def update_category(category_id: int, data: CategoryUpdate) -> Category:
		"""更新分类（仅更新非 None 字段）"""
		category = await CategoryService.get_category_by_id(category_id)
		update_data = data.model_dump(exclude_none=True)

		if not update_data:
			return category

		try:
			await category.update_from_dict(update_data).save()
			return category
		except IntegrityError:
			raise ServiceError("更新失败，分类名称或别名可能重复", code="CONFLICT", status_code=409)

	@staticmethod
	async def delete_category(category_id: int) -> bool:
		"""删除分类"""
		category = await CategoryService.get_category_by_id(category_id)
		await category.delete()
		return True

	@staticmethod
	async def list_categories(limit: int = 20, offset: int = 0) -> list[Category]:
		"""获取分类列表"""
		return await Category.all().order_by("name").offset(offset).limit(limit)
