from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from ..models import PostStatus


class PostCreate(BaseModel):
    title: str = Field(..., max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = Field(None)
    content: str = Field(...)
    status: PostStatus = Field(PostStatus.DRAFT)
    is_featured: bool = Field(False)
    category_id: Optional[int] = Field(None)
    model_config = ConfigDict(from_attributes=True)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = Field(None)
    content: Optional[str] = Field(None)
    status: Optional[PostStatus] = Field(None)
    is_featured: Optional[bool] = Field(None)
    category_id: Optional[int] = Field(None)
    published_at: Optional[datetime] = Field(None)
    model_config = ConfigDict(from_attributes=True)


class PostBrief(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    status: PostStatus
    is_featured: bool
    view_count: int
    category_id: Optional[int] = None
    author_id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PostDetail(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    status: PostStatus
    is_featured: bool
    view_count: int
    category_id: Optional[int] = None
    author_id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PostSearch(BaseModel):
    keyword: Optional[str] = Field(None)
    category_id: Optional[int] = Field(None)
    author_id: Optional[int] = Field(None)
    status: Optional[PostStatus] = Field(None)
    is_featured: Optional[bool] = Field(None)
    
    # 让 Pydantic 接受来自 Query 参数的数据
    model_config = ConfigDict(from_attributes=True)