from typing import List, Optional, Any
from datetime import timezone, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.expressions import Q

from .models import Post, PostStatus, Tag, User, UserLevel, ServiceError

# --- Service 层实现 ---
class PostService:
    @staticmethod
    async def create(
        title: str,
        slug: str,
        content: str,
        category_id: int = None,
        excerpt: str = None,
        tag_ids: List[int] = None,
        is_featured: bool = False,
        is_comment_enabled: bool = True,
    ) -> Post:
        """创建文章草稿，处理 Slug 重复或分类不存在的情况"""
        try:
            post = await Post.create(
                title=title,
                slug=slug,
                content=content,
                category_id=category_id,
                excerpt=excerpt,
                is_featured=is_featured,
                is_comment_enabled=is_comment_enabled,
                status=PostStatus.DRAFT,
            )
            if tag_ids:
                await post.tags.add(*tag_ids)
            return post
        except IntegrityError as e:
            raise ServiceError(f"创建失败：Slug '{slug}' 已存在或分类 ID 无效", detail=str(e))

    @staticmethod
    async def get_by_id(post_id: int) -> Post:
        """通过 ID 获取文章，包含分类和标签，不存在则抛出 ServiceError"""
        try:
            return await Post.get(id=post_id).prefetch_related("category", "tags")
        except DoesNotExist:
            raise ServiceError(f"找不到 ID 为 {post_id} 的文章")

    @staticmethod
    async def get_by_slug(slug: str) -> Post:
        """通过 URL Slug 查找文章"""
        try:
            return await Post.get(slug=slug).prefetch_related("category", "tags")
        except DoesNotExist:
            raise ServiceError(f"路径 '{slug}' 对应的文章不存在")

    @staticmethod
    async def get_all(
        status: Optional[PostStatus] = PostStatus.PUBLISHED, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Post]:
        """按状态分页查询文章，默认只查询已发布文章"""
        query = Post.all()
        if status is not None:
            query = query.filter(status=status)
        
        return await query.limit(limit).offset(offset).prefetch_related(
            "category", "tags", "author"
        ).order_by("-created_at")

    @staticmethod
    async def update(post_id: int, **kwargs) -> Post:
        """更新文章字段，支持关联标签的增量更新"""
        post = await PostService.get_by_id(post_id)
        tag_ids = kwargs.pop("tag_ids", None)

        try:
            for key, value in kwargs.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            
            await post.save()

            if tag_ids is not None:
                await post.tags.clear()
                if tag_ids:
                    await post.tags.add(*tag_ids)
            
            return post
        except IntegrityError as e:
            raise ServiceError("更新失败：冲突的字段值（如 Slug 重复）", detail=str(e))

    @staticmethod
    async def publish(post_id: int) -> Post:
        """正式发布文章，并更新发布时间戳"""
        post = await PostService.get_by_id(post_id)
        if post.status == PostStatus.PUBLISHED:
            return post

        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.now(timezone.utc)
        await post.save()
        return post

    @staticmethod
    async def delete(post_id: int) -> None:
        """物理删除文章"""
        post = await PostService.get_by_id(post_id)
        await post.delete()

    @staticmethod
    async def increment_view_count(post_id: int) -> Post:
        """文章阅读数自增"""
        post = await PostService.get_by_id(post_id)
        post.view_count += 1
        await post.save()
        return post

    @staticmethod
    async def search(keyword: str, status: PostStatus = None) -> List[Post]:
        """模糊搜索标题或摘要中的关键词"""
        query = Post.filter(Q(title__icontains=keyword) | Q(excerpt__icontains=keyword))
        if status is not None:
            query = query.filter(status=status)
        return await query.prefetch_related("category", "tags")


class TagService:
    @staticmethod
    async def create(name: str, slug: str, description: str = None) -> Tag:
        """创建新标签"""
        try:
            return await Tag.create(name=name, slug=slug, description=description)
        except IntegrityError:
            raise ServiceError("标签名称或 Slug 已存在")

    @staticmethod
    async def get_by_id(tag_id: int) -> Tag:
        """获取标签详情"""
        try:
            return await Tag.get(id=tag_id)
        except DoesNotExist:
            raise ServiceError(f"标签 ID {tag_id} 不存在")

    @staticmethod
    async def get_all() -> List[Tag]:
        """列出所有标签"""
        return await Tag.all()

    @staticmethod
    async def update(tag_id: int, **kwargs) -> Tag:
        """更新标签元数据"""
        tag = await TagService.get_by_id(tag_id)
        try:
            for key, value in kwargs.items():
                if hasattr(tag, key):
                    setattr(tag, key, value)
            await tag.save()
            return tag
        except IntegrityError:
            raise ServiceError("标签更新冲突：名称或 Slug 已被占用")

    @staticmethod
    async def delete(tag_id: int) -> None:
        """删除标签（不会删除关联的文章）"""
        tag = await TagService.get_by_id(tag_id)
        await tag.delete()


class UserService:
    password_hash_function = PasswordHash.recommended()
    SECRET_KEY = "your-secret-key-here" 
    ALGORITHM = "HS256"

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None):
        """生成 JWT 访问令牌"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与哈希值是否匹配"""
        return cls.password_hash_function.verify(plain_password, hashed_password)

    @staticmethod
    async def authenticate_user(username: str, password: str) -> User:
        """验证用户名和密码，成功返回 User 对象，失败抛出 ServiceError"""
        try:
            user = await User.get(username=username)
            if UserService.verify_password(password, user.password_hash):
                return user
            raise ServiceError("用户名或密码错误")
        except DoesNotExist:
            raise ServiceError(f"用户 '{username}' 不存在")

    @staticmethod
    async def create_user(
        username: str, email: str, password: str, level: UserLevel = UserLevel.REGULAR
    ) -> User:
        """注册新用户，自动对密码进行哈希处理"""
        try:
            password_hash = UserService.password_hash_function.hash(password)
            now = datetime.now(timezone.utc)
            new_user = await User.create(
                username=username,
                email=email,
                password_hash=password_hash,
                level=level,
                created_at=now,
                updated_at=now,
            )
            
            if new_user is None:
                raise ServiceError("创建用户失败 可能是数据库问题")
            
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
    async def update_user(user_id: int, update_data: dict) -> User:
        """
        更新用户信息。
        :param user_id: 用户ID
        :param update_data: 已经通过 model_dump(exclude_unset=True) 过滤后的字典
        """
        user = await UserService.get_user_by_id(user_id)
        
        # 1. 过滤黑名单：防止恶意修改权限、ID或密码
        forbidden = {"username", "level", "id", "created_at", "password_hash", "password"}
        
        # 移除字典中可能存在的敏感键，而不是直接报错
        safe_data = {k: v for k, v in update_data.items() if k not in forbidden}

        if not safe_data:
            return user # 如果过滤后没东西了，直接返回原对象

        try:
            for key, value in safe_data.items():
                setattr(user, key, value)
            
            user.updated_at = datetime.now(timezone.utc)
            
            await user.save()
            return user
            
        except IntegrityError:
            raise ServiceError("更新失败")


    @staticmethod
    async def change_password(user_id: int, old_password: str, new_password: str) -> None:
        """修改密码，需验证旧密码"""
        user = await UserService.get_user_by_id(user_id)
        
        if not UserService.password_hash_function.verify(old_password, user.password_hash):
            raise ServiceError("旧密码验证不通过")

        user.password_hash = UserService.password_hash_function.hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """注销/删除用户"""
        user = await UserService.get_user_by_id(user_id)
        await user.delete()