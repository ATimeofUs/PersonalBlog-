from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Annotated


# ============ Token ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============ User（隐私数据，区分 In/Out） ============

class UserIn(BaseModel):
    """用户注册/创建"""
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    profile_photo: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)  # 增加最大长度限制


class UserUpdate(BaseModel):
    """用户信息更新（全部可选）"""
    username: Annotated[str | None, Field(max_length=50)] = None
    description: Annotated[str | None, Field(max_length=500)] = None
    email: Annotated[EmailStr | None, Field()] = None
    


class UserOut(BaseModel):
    """用户输出（不含密码）"""
    id: int
    username: str
    email: EmailStr
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    level: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    """用户简要信息（嵌套在文章里用）"""
    id: int
    username: str
    profile_photo: Optional[str] = None

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# ============ Category（非隐私，一套搞定） ============

class CategoryBase(BaseModel):
    """分类 - 创建/更新通用"""
    name: str = Field(..., max_length=50)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None


class Category(CategoryBase):
    """分类 - 完整输出"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Tag（非隐私，一套搞定） ============

class TagBase(BaseModel):
    """标签 - 创建/更新通用"""
    name: str = Field(..., max_length=50)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None


class Tag(TagBase):
    """标签 - 完整输出"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Post（内容较多，分层处理） ============

class PostCreate(BaseModel):
    """创建文章"""
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    excerpt: Optional[str] = None
    content: str
    status: int = Field(default=0, ge=0, le=1)  # 0=草稿, 1=已发布
    is_featured: bool = False
    category_id: Optional[int] = None
    tag_ids: list[int] = Field(default_factory=list)


class PostUpdate(BaseModel):
    """更新文章（全部可选）"""
    title: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = None
    content: Optional[str] = None
    status: Optional[int] = Field(None, ge=0, le=1)
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None
    tag_ids: Optional[list[int]] = None


class PostOut(BaseModel):
    """文章完整输出（带关联数据）"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    status: int
    is_featured: bool
    view_count: int

    # 关联对象展开，不只是返回 id
    category: Optional[Category] = None
    author: UserBrief
    tags: list[Tag] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostBrief(BaseModel):
    """文章列表/摘要（不含正文，列表页用）"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    status: int
    is_featured: bool
    view_count: int

    category: Optional[Category] = None
    author: UserBrief
    tags: list[Tag] = Field(default_factory=list)

    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 通用分页 ============

class Pagination(BaseModel):
    """分页响应包装"""
    total: int
    page: int
    page_size: int
    items: list  # 具体类型在路由层用泛型或直接标注