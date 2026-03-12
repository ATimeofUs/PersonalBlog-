from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, Query

from ..services import UserService
from ..schemas.pydantic_model import UserOut, UserCreate, ChangePassword, UserBrief, UserUpdate
from ..core import get_current_user, require_admin, require_super_admin
from ..models import UserLevel
from ..core.media_storage import delete_avatar_file, save_avatar_file

router = APIRouter(prefix="/user", tags=["user"])


class UserDependency:
    """用户相关的依赖项集合"""

    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    READ_CHUNK_SIZE = 8192
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
        if not avatar.filename:
            raise HTTPException(status_code=400, detail="缺少文件名")
        file_extension = Path(avatar.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的图片格式")
        if avatar.content_type not in self.allowed_content_types:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        return avatar

    async def get_avatar_extension(self, avatar: UploadFile) -> str:
        content_type_extension = self.allowed_content_types.get(avatar.content_type)
        original_extension = Path(avatar.filename or "").suffix.lower()
        if content_type_extension == ".jpg" and original_extension == ".jpeg":
            return ".jpeg"
        return content_type_extension or original_extension


user_dependency = UserDependency()


# ── 1. 查询接口 ────────────────────────────────────────────────────────────────

@router.get("/detail", response_model=UserOut)
async def read_users_detail(current_user: Annotated[UserOut, Depends(get_current_user)]):
    return current_user


@router.get("/brief", response_model=UserBrief)
async def read_user_brief(current_user: Annotated[UserOut, Depends(get_current_user)]):
    return current_user


# ── 2. 更新接口 ────────────────────────────────────────────────────────────────

@router.post("/change_password", response_model=bool)
async def change_password(
    data: Annotated[ChangePassword, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    try:
        await UserService.change_password(user_id=current_user.id, data=data)
        return True
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/update", response_model=UserOut)
async def update_user(
    data: Annotated[UserUpdate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    try:
        return await UserService.update_user(user_id=current_user.id, data=data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    avatar: Annotated[UploadFile, Depends(user_dependency.validate_avatar_upload)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    file_extension = await user_dependency.get_avatar_extension(avatar)
    avatar_path = None
    try:
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
        updated_user = await UserService.update_profile_photo(
            user_id=current_user.id, profile_photo_path=avatar_path
        )
    except Exception as exc:
        delete_avatar_file(avatar_path)
        raise HTTPException(status_code=400, detail=str(exc))

    # 删除旧头像
    if current_user.profile_photo and current_user.profile_photo != avatar_path:
        delete_avatar_file(current_user.profile_photo)

    return updated_user


# ── 3. 管理员接口 ──────────────────────────────────────────────────────────────

@router.get("/show_user", response_model=list[UserBrief])
async def show_user(
    current_user: Annotated[UserOut, Depends(require_admin)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await UserService.get_all_users(limit=limit, offset=offset)


@router.post("/delete_user", response_model=bool)
async def delete_user(
    user_id: Annotated[int, Body(..., embed=True)],
    current_user: Annotated[UserOut, Depends(require_super_admin)],
):
    try:
        return await UserService.delete_user(user_id=user_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/create_user", response_model=UserOut)
async def create_user(
    data: Annotated[UserCreate, Body(...)],
    current_user: Annotated[UserOut, Depends(require_admin)],  # 测试阶段注释掉
):
    try:
        return await UserService.create_user(data=data, level=UserLevel.REGULAR)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    
@router.post("/upgrade_user_level", response_model=UserOut)
async def upgrade_user_level(
    user_id: Annotated[int, Body(..., embed=True)],
    new_level: Annotated[UserLevel, Body(..., embed=True)],
    current_user: Annotated[UserOut, Depends(require_super_admin)],
):
    try:
        return await UserService.upgrade_user_level(user_id=user_id, new_level=new_level)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))