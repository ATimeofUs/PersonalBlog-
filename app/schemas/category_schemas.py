from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
	"""创建分类"""

	name: str = Field(..., min_length=1, max_length=50)
	slug: str = Field(..., min_length=1, max_length=50)
	description: Optional[str] = Field(None)
	model_config = ConfigDict(from_attributes=True)


class CategoryUpdate(BaseModel):
	"""更新分类"""

	name: Optional[str] = Field(None, min_length=1, max_length=50)
	slug: Optional[str] = Field(None, min_length=1, max_length=50)
	description: Optional[str] = Field(None)
	model_config = ConfigDict(from_attributes=True)


class CategoryBrief(BaseModel):
	"""分类简要信息"""

	id: int
	name: str
	slug: str
	model_config = ConfigDict(from_attributes=True)


class CategoryDetail(BaseModel):
	"""分类详情"""

	id: int
	name: str
	slug: str
	description: Optional[str] = None
	created_at: datetime
	updated_at: datetime
	model_config = ConfigDict(from_attributes=True)


class CategorySearch(BaseModel):
	"""分类搜索"""

	limit: int = Field(20, ge=1, le=100)
	offset: int = Field(0, ge=0)
	model_config = ConfigDict(from_attributes=True)
