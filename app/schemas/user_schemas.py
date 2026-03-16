from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, Annotated

# 统一约束
USERNAME_FIELD = Field(..., min_length=4, max_length=50)
PASSWORD_FIELD = Field(..., min_length=6, max_length=30)


class UserCreate(BaseModel):
    """注册时需要密码"""
    username: Annotated[str, USERNAME_FIELD]
    email: EmailStr
    password: Annotated[str, PASSWORD_FIELD]
    description: Optional[str] = Field(None, max_length=1000)
    profile_photo: Optional[str] = Field(None, max_length=255)
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    """更新信息：所有字段设为可选"""
    # 注意：这里不带 username，因为用户名通常不允许修改
    description: Optional[Annotated[str, Field(max_length=1000)]] = None
    email: Optional[EmailStr] = None
    profile_photo: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserData(BaseModel):
    """完整的用户信息输出"""
    id : int 
    username: Annotated[str, USERNAME_FIELD]
    email: EmailStr
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    level: int 
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserBrief(BaseModel):
    """嵌套在文章中的作者信息"""
    id: int
    username: str
    profile_photo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserChangePassword(BaseModel):
    """密码修改"""
    old_password: Annotated[str, PASSWORD_FIELD]
    new_password: Annotated[str, PASSWORD_FIELD]
    model_config = ConfigDict(from_attributes=True)
    