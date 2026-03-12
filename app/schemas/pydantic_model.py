from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Annotated


# ============ Token ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============ User ============

class UserCreate(BaseModel):
    """用户注册/创建"""
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    description: Optional[str] = Field(None, max_length=1000)  # 补上缺失的字段
    profile_photo: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    """用户信息更新（全部可选）
    注意：username 不可通过此接口修改（由后端安全策略决定，不在此暴露）
    """
    description: Annotated[str | None, Field(max_length=1000)] = None
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


# ============ Category ============

class CategoryCreate(BaseModel):
    """分类 - 创建"""
    name: str = Field(..., max_length=50)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    """分类 - 更新（全部可选）"""
    name: Annotated[str | None, Field(max_length=50)] = None
    slug: Annotated[str | None, Field(max_length=50)] = None
    description: Optional[str] = None


class CategoryOut(CategoryCreate):
    """分类 - 输出"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryBrief(BaseModel):
    """分类简要信息（嵌套在文章里用）"""
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True

# ============ Post ============

class PostCreate(BaseModel):
    """文章 - 创建"""
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    excerpt: Optional[str] = None
    content: str = Field(..., description="文章内容，支持 Markdown 格式")
    status: int = Field(0, description="0-草稿, 1-已发布")
    is_featured: bool = False
    category_id: Optional[int] = None


class PostUpdate(BaseModel):
    """文章 - 更新（全部可选）"""
    title: Annotated[str | None, Field(max_length=255)] = None
    slug: Annotated[str | None, Field(max_length=255)] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    status: Optional[int] = Field(None, description="0-草稿, 1-已发布")
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None


class PostOut(BaseModel):
    """文章 - 展示给用户的输出（嵌套关联对象）"""
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    status: int
    is_featured: bool
    view_count: int
    author: UserBrief
    category: Optional[CategoryBrief] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostBrief(BaseModel):
    """文章 - 列表/摘要输出（不含正文）"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    status: int
    is_featured: bool
    view_count: int
    author: UserBrief
    category: Optional[CategoryBrief] = None
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


POST_LIMIT = 20
class PostQuery(BaseModel):
    """通用文章查询参数，用于搜索、列表、按用户筛选等接口"""
    keyword:     Optional[str] = Field(None, max_length=100, description="标题/摘要关键词")
    category_id: Optional[int] = Field(None, ge=1)
    status:      Optional[int] = Field(None, ge=0, le=1, description="0-草稿 1-已发布")
    author_id:   Optional[int] = Field(None, ge=1)
    limit:       int           = Field(POST_LIMIT, ge=1, le=100)
    offset:      int           = Field(0, ge=0)
