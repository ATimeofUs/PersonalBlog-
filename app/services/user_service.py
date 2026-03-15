"""
功能：封装用户相关的核心业务逻辑，包括 CRUD 操作、权限变更及密码管理。
"""

import logging
import os
from typing import List
from pwdlib import PasswordHash
from tortoise.exceptions import DoesNotExist, IntegrityError

from ..models import User, UserLevel, ServiceError
from ..schemas.user_model import UserCreate, UserUpdate, UserChangePassword

PASSWORD_HASH = PasswordHash.recommended()

class UserService:
    """
    用户业务层类
    
    所有方法均为静态方法（@staticmethod），负责处理 User 模型的增删改查及业务校验。
    """

    @staticmethod
    async def authenticate_user(username: str, password: str) -> User:
        """验证用户和密码"""
        user_db = await UserService.get_user_by_username(username=username)
        
        if not PASSWORD_HASH.verify(password=password, hash=user_db.password_hash):
            raise ServiceError(message="错误密码" ,status_code=401)
        
        return user_db

    @staticmethod
    async def create_user(data: UserCreate, level: UserLevel = UserLevel.REGULAR) -> User:
        """
        注册新用户并持久化到数据库。
        
        Args:
            data (UserCreate): 包含用户名、邮箱、原始密码等信息的 Pydantic 模型。
            level (UserLevel): 用户初始等级，默认为普通用户。
            
        Returns:
            User: 创建成功的 Tortoise ORM 用户对象。
            
        Raises:
            ServiceError: 如果用户名或邮箱在数据库中已存在。
        """
        try:
            # 1. 密码加盐哈希处理，确保数据库不存储明文
            password_hash = PASSWORD_HASH.hash(data.password)
            
            # 2. 创建数据库记录
            new_user = await User.create(
                username=data.username,
                email=data.email,
                password_hash=password_hash,
                level=level,
                description="", # 默认空字符串
                profile_photo=None, # 默认无头像
            )
            return new_user
        except IntegrityError:
            # 通常由数据库唯一索引 (Unique Index) 触发
            raise ServiceError("用户名或邮箱已被注册", code=409)

    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        """
        通过主键 ID 精确查找用户。
        
        Args:
            user_id (int): 数据库自增 ID。
            
        Returns:
            User: 找到的用户对象。
            
        Raises:
            ServiceError: 当 ID 不存在时。
        """
        try:
            return await User.get(id=user_id)
        except DoesNotExist:
            raise ServiceError("该用户不存在", code=404)

    @staticmethod
    async def get_user_by_username(username: str) -> User:
        """
        通过用户名查找用户。
        
        Args:
            username (str): 用户名。
            
        Returns:
            User: 找到的用户对象。
        """
        try:
            return await User.get(username=username)
        except DoesNotExist:
            raise ServiceError("该用户不存在", code=404)

    @staticmethod
    async def update_user(user_id: int, data: UserUpdate) -> User:
        """
        局部更新用户信息。
        
        仅更新前端传入的字段，未传字段保持不变。
        
        Args:
            user_id (int): 目标用户 ID。
            data (UserUpdate): 包含可选更新字段的模型。
            
        Returns:
            User: 更新后的用户对象。
        """
        # 1. 先验证用户是否存在
        user = await UserService.get_user_by_id(user_id)

        # 2. exclude_unset=True 是关键：只提取前端 JSON 中实际存在的 Key，防止 None 覆盖数据库原值
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return user

        try:
            # 3. 动态设置属性
            for key, value in update_data.items():
                setattr(user, key, value)
            
            await user.save()
            return user
        except IntegrityError:
            raise ServiceError("更新失败，邮箱可能已被占用", code=409)

    @staticmethod
    async def change_password(user_id: int, data: UserChangePassword) -> User:
        """
        安全修改密码逻辑。
        
        包含：旧密码验证 -> 新密码哈希 -> 存储。
        
        Args:
            user_id (int): 用户 ID。
            data (UserChangePassword): 包含 old_password 和 new_password。
        """
        user = await UserService.get_user_by_id(user_id)

        # 验证旧密码：将明文与数据库哈希值比对
        if not PASSWORD_HASH.verify(data.old_password, user.password_hash):
            raise ServiceError("旧密码验证不通过", code=401)

        # 存储新密码的哈希
        user.password_hash = PASSWORD_HASH.hash(data.new_password)
        await user.save()
        
        return User

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        """
        物理删除用户。
        
        Args:
            user_id (int): 要删除的用户 ID。
            
        Returns:
            bool: 成功返回 True。
        """
        user = await UserService.get_user_by_id(user_id)
        await user.delete()
        return True

    @staticmethod
    async def update_profile_photo(user_id: int, profile_photo_path: str, old_photo_path: str | None) -> User:
        """
        快速更新头像路径。
        
        Args:
            user_id (int): 用户 ID。
            profile_photo_path (str): 相对路径（通常由 media_storage 处理后传入）。
            old_photo_path (str | None): 旧头像路径，用于后续清理。
        """
        user = await UserService.get_user_by_id(user_id=user_id)
        
        logging.info("正在更新用户 %d 的头像，旧路径：%s，新路径：%s", user_id, old_photo_path, profile_photo_path)
                
        user.profile_photo = profile_photo_path
        try:
            logging.info("正在保存用户 %d 的新头像路径到数据库 %s ，老的路径是 %s", user_id, profile_photo_path, old_photo_path)
            await user.save()
            return user
        except IntegrityError:
            logging.error("更新用户 %d 头像失败: %s", user_id, "数据库错误")
            raise ServiceError("头像更新失败")

    @staticmethod
    async def get_all_users(limit: int = 20, offset: int = 0) -> List[User]:
        """
        分页查询用户列表，按注册时间倒序。
        
        Args:
            limit (int): 返回数量限制。
            offset (int): 偏移量（用于分页）。
        """
        return await User.all().limit(limit).offset(offset).order_by("-created_at")
    
    @staticmethod 
    async def upgrade_user_level(user_id: int, new_level: UserLevel) -> User:
        """
        手动调整用户等级（如：普通用户 -> 管理员）。
        
        Args:
            user_id (int): 用户 ID。
            new_level (UserLevel): 目标等级（Enum）。
        """
        user = await UserService.get_user_by_id(user_id)
        
        # 虽然 get_user_by_id 内部会 raise，但此处加个判断更严谨
        if user is None:
            raise ServiceError("用户不存在")
        
        user.level = new_level
        try:
            await user.save()
            return user
        except IntegrityError:
            raise ServiceError("用户等级更新失败")