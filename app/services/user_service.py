from typing import List
from datetime import timezone, datetime

from pwdlib import PasswordHash
from tortoise.exceptions import DoesNotExist, IntegrityError

from ..models.models import User, UserLevel, ServiceError
from ..schemas.pydantic_model import UserCreate, UserUpdate, ChangePassword


class UserService:
    password_hash_function = PasswordHash.recommended()

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与哈希值是否匹配"""
        return cls.password_hash_function.verify(plain_password, hashed_password)

    @staticmethod
    async def authenticate_user(username: str, password: str) -> User:
        """验证用户名和密码，成功返回 User 对象，失败抛出 ServiceError
        注：此方法保留散参数，因为调用方来自 auth_router（OAuth2 表单），不经过 schema）
        """
        try:
            user = await User.get(username=username)
            if UserService.verify_password(password, user.password_hash):
                return user
            raise ServiceError("用户名或密码错误")
        except DoesNotExist:
            raise ServiceError(f"用户 '{username}' 不存在")

    @staticmethod
    async def create_user(data: UserCreate, level: UserLevel = UserLevel.REGULAR) -> User:
        """注册新用户，自动对密码进行哈希处理"""
        try:
            password_hash = UserService.password_hash_function.hash(data.password)
            now = datetime.now(timezone.utc)
            new_user = await User.create(
                username=data.username,
                email=data.email,
                password_hash=password_hash,
                level=level,
                description=data.description,
                profile_photo=data.profile_photo,
                created_at=now,
                updated_at=now,
            )
            return new_user
        except IntegrityError:
            raise ServiceError("用户名或邮箱已被注册")

    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        """通过 ID 获取用户信息"""
        try:
            return await User.get(id=user_id)
        except DoesNotExist:
            raise ServiceError("该用户不存在")

    @staticmethod
    async def get_user_by_username(username: str) -> User:
        """通过用户名称获得用户"""
        try:
            return await User.get(username=username)
        except DoesNotExist:
            raise ServiceError("该用户不存在")

    @staticmethod
    async def update_user(user_id: int, data: UserUpdate) -> User:
        """更新用户信息，只更新 schema 中实际传入的字段"""
        user = await UserService.get_user_by_id(user_id)

        # exclude_unset=True 只取前端实际传入的字段，避免用 None 覆盖已有数据
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return user

        try:
            for key, value in update_data.items():
                setattr(user, key, value)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()
            return user
        except IntegrityError:
            raise ServiceError("更新失败，邮箱可能已被占用")

    @staticmethod
    async def change_password(user_id: int, data: ChangePassword) -> None:
        """修改密码，需验证旧密码"""
        user = await UserService.get_user_by_id(user_id)

        if not UserService.password_hash_function.verify(data.old_password, user.password_hash):
            raise ServiceError("旧密码验证不通过")

        user.password_hash = UserService.password_hash_function.hash(data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        """注销/删除用户，成功返回 True"""
        user = await UserService.get_user_by_id(user_id)
        await user.delete()
        return True

    @staticmethod
    async def update_profile_photo(user_id: int, profile_photo_path: str) -> User:
        """更新头像路径"""
        user = await UserService.get_user_by_id(user_id=user_id)
        user.profile_photo = profile_photo_path
        try:
            await user.save()
            return user
        except IntegrityError:
            raise ServiceError("头像更新失败")

    @staticmethod
    async def get_all_users(limit: int = 20, offset: int = 0) -> List[User]:
        """分页获取用户列表"""
        return await User.all().limit(limit).offset(offset).order_by("-created_at")
    
    
    @staticmethod 
    async def upgrade_user_level(user_id: int, new_level: UserLevel) -> User:
        """升级用户等级"""
        user = await UserService.get_user_by_id(user_id)
        
        if user is None:
            raise ServiceError("用户不存在")
        
        user.level = new_level
        user.updated_at = datetime.now(timezone.utc)
        try:
            await user.save()
            return user
        except IntegrityError:
            raise ServiceError("用户等级更新失败")