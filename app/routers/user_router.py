"""
模块：UserRouter
项目：PersonalBlog
功能：定义用户相关的 Web API 路由，包含：
    - 个人资料查询与更新 (Detail/Update/Avatar)
    - 安全管理 (Password)
    - 管理员管理行为 (List/Create/Delete/Upgrade)
开发者：ping (Liu Junjie)
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, Query

from ..services import UserService
from ..schemas.user_model import (
    UserData,
    UserCreate,
    UserChangePassword,
    UserBrief,
    UserUpdate,
)
from ..core import get_current_user, require_admin, require_super_admin
from ..models import UserLevel
from ..core.media_storage import delete_avatar_file, save_avatar_file

# 定义路由组：所有路径前缀为 /user，在 Swagger 文档中归类为 "user" 标签
router = APIRouter(prefix="/user", tags=["user"])


class UserDependency:
    """
    用户业务依赖项

    封装了头像上传的限制参数和校验逻辑，保持路由代码简洁。
    """

    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 限制 5MB
    READ_CHUNK_SIZE = 8192  # 分块读取大小 (8KB)

    # 允许的 MIME 类型与后缀映射
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    def __init__(self):
        self.max_image_size = self.MAX_IMAGE_SIZE
        self.read_chunk_size = self.READ_CHUNK_SIZE
        self.allowed_content_types = self.ALLOWED_CONTENT_TYPES
        self.allowed_extensions = self.ALLOWED_EXTENSIONS

    async def validate_avatar_upload(
        self,
        avatar: Annotated[UploadFile, File(...)],
    ) -> UploadFile:
        """验证上传的文件是否为合法的图片"""
        if not avatar.filename:
            raise HTTPException(status_code=400, detail="缺少文件名")

        file_extension = Path(avatar.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        if avatar.content_type not in self.allowed_content_types:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

        return avatar

    async def get_avatar_extension(self, avatar: UploadFile) -> str:
        """根据 Content-Type 获取规范的扩展名"""
        content_type_extension = self.allowed_content_types.get(avatar.content_type)
        original_extension = Path(avatar.filename or "").suffix.lower()

        # 特殊处理 jpeg 别名
        if content_type_extension == ".jpg" and original_extension == ".jpeg":
            return ".jpeg"
        return content_type_extension or original_extension


# 实例化依赖工具
user_dependency = UserDependency()


# ── 1. 查询接口 ────────────────────────────────────────────────────────────────


@router.get("/detail", response_model=UserData)
async def read_users_detail(
    current_user: Annotated[UserData, Depends(get_current_user)],
) -> UserData:
    """获取当前登录用户的完整个人资料"""
    return current_user


@router.get("/brief", response_model=UserBrief)
async def read_user_brief(current_user: Annotated[UserData, Depends(get_current_user)]) -> UserBrief:
    """获取当前登录用户的简要信息（常用于前端顶栏头像显示）"""
    return current_user


# ── 2. 更新接口 ────────────────────────────────────────────────────────────────


@router.post("/change_password", response_model=bool)
async def change_password(
    data: Annotated[UserChangePassword, Body(...)],
    current_user: Annotated[UserData, Depends(get_current_user)],
):
    """修改当前用户的登录密码，需校验旧密码"""
    try:
        await UserService.change_password(user_id=current_user.id, data=data)
        return True
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/update", response_model=UserData)
async def update_user(
    data: Annotated[UserUpdate, Body(...)],
    current_user: Annotated[UserData, Depends(get_current_user)],
):
    """更新当前用户的基本资料（如邮箱、简介等）"""
    try:
        return await UserService.update_user(user_id=current_user.id, data=data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/avatar", response_model=UserData)
async def upload_avatar(
    avatar: Annotated[UploadFile, Depends(user_dependency.validate_avatar_upload)],
    current_user: Annotated[UserData, Depends(get_current_user)],
):
    """
    上传并更换个人头像

    流程：验证格式 -> 保存新图 -> 更新数据库 -> 删除物理旧图
    """
    file_extension = await user_dependency.get_avatar_extension(avatar)
    avatar_path = None

    try:
        # 1. 保存新文件到磁盘
        avatar_path = await save_avatar_file(
            avatar,
            file_extension=file_extension,
            max_size=user_dependency.max_image_size,
            read_chunk_size=user_dependency.read_chunk_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        if avatar_path:
            delete_avatar_file(avatar_path)
        raise HTTPException(status_code=500, detail="保存头像失败")

    try:
        # 2. 更新数据库记录
        updated_user = await UserService.update_profile_photo(
            user_id=current_user.id, profile_photo_path=avatar_path
        )
    except Exception as exc:
        # 如果数据库更新失败，必须清理刚保存的物理文件以免产生垃圾
        delete_avatar_file(avatar_path)
        raise HTTPException(status_code=400, detail=str(exc))

    # 3. 成功后，清理该用户之前的旧头像文件
    if current_user.profile_photo and current_user.profile_photo != avatar_path:
        delete_avatar_file(current_user.profile_photo)

    return updated_user


# ── 3. 管理员接口 ──────────────────────────────────────────────────────────────


@router.get("/show_user", response_model=list[UserBrief])
async def show_user(
    current_user: Annotated[UserData, Depends(require_admin)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """[管理员] 预览用户列表，支持分页"""
    return await UserService.get_all_users(limit=limit, offset=offset)


@router.post("/delete_user", response_model=bool)
async def delete_user(
    user_id: Annotated[int, Body(..., embed=True)],
    current_user: Annotated[UserData, Depends(require_super_admin)],
):
    """[超级管理员] 物理删除指定用户"""
    try:
        return await UserService.delete_user(user_id=user_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/create_user", response_model=UserData)
async def create_user(
    data: Annotated[UserCreate, Body(...)],
    current_user: Annotated[UserData, Depends(require_admin)],
):
    """[管理员] 手动创建新用户"""
    try:
        return await UserService.create_user(data=data, level=UserLevel.REGULAR)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/upgrade_user_level", response_model=UserData)
async def upgrade_user_level(
    user_id: Annotated[int, Body(..., embed=True)],
    new_level: Annotated[UserLevel, Body(..., embed=True)],
    current_user: Annotated[UserData, Depends(require_super_admin)],
):
    """[超级管理员] 调整指定用户的权限等级（如提拔为管理员）"""
    try:
        return await UserService.upgrade_user_level(
            user_id=user_id, new_level=new_level
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
