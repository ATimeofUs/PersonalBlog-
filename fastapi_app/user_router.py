from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile

from my_dataset import UserService
from .model import UserOut, UserIn, ChangePassword, UserBrief, UserUpdate
from .auth_router import get_current_user, require_admin, require_super_admin
from my_dataset import UserLevel
from .media_storage import delete_avatar_file, save_avatar_file

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

    # --- 关键修改：去掉 Depends()，让 FastAPI 识别为 Body ---
    async def get_avatar_extension(self, avatar: UploadFile) -> str:
        content_type_extension = self.allowed_content_types.get(avatar.content_type)
        original_extension = Path(avatar.filename or "").suffix.lower()
        if content_type_extension == ".jpg" and original_extension == ".jpeg":
            return ".jpeg"
        return content_type_extension or original_extension


user_dependency = UserDependency()

## 1. 用户查询接口 (保留 GET)
@router.get("/detail", response_model=UserOut)
async def read_users_detail(current_user: Annotated[UserIn, Depends(get_current_user)]):
    return current_user

@router.get("/brief", response_model=UserBrief)
async def read_user_brief(current_user: Annotated[UserIn, Depends(get_current_user)]):
    return current_user



## 2. 更新与操作接口 (统一为 Body)
# 修改密码 (本身就是模型，默认是 Body)
@router.post("/change_password", response_model=bool)
async def change_password(
    password_data: Annotated[ChangePassword, Body(...)],
    current_user: Annotated[UserIn, Depends(get_current_user)],
):  
    try:
        await UserService.change_password(
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
        )
        return True
    except Exception as exc:
        print("修改密码错误: ", exc)
        raise HTTPException(status_code=400, detail="修改密码失败")
    

# 修改用户信息 (使用 Body)
@router.post("/update", response_model=UserOut)
async def update_user(
    user_data: Annotated[UserUpdate, Body(...)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    update_data = user_data.model_dump(exclude_unset=True)
    if not update_data:
        return current_user

    updated_user = await UserService.update_user(
        user_id=current_user.id,
        update_data=update_data,
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="修改失败")
    return updated_user



# 头像上传 (Multipart/form-data 属于特殊的 Body)
@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    avatar: Annotated[UploadFile, Depends(user_dependency.validate_avatar_upload)],
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    file_extension = await user_dependency.get_avatar_extension(avatar)
    try:
        avatar_path = await save_avatar_file(
            avatar,
            file_extension=file_extension,
            max_size=user_dependency.max_image_size,
            read_chunk_size=user_dependency.read_chunk_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    updated_user = await UserService.update_user(user_id=current_user.id, profile_photo=avatar_path)
    if not updated_user:
        delete_avatar_file(avatar_path)
        raise HTTPException(status_code=400, detail="头像保存失败")

    if current_user.profile_photo and current_user.profile_photo != avatar_path:
        delete_avatar_file(current_user.profile_photo)
    return updated_user

## 3. 管理员接口
@router.get("/show_user", response_model=list[UserBrief])
async def show_user(current_user: Annotated[UserIn, Depends(require_admin)]):
    return await UserService.get_all_users()


# 删除用户：将单字段 user_id 强制转为 Body
@router.post("/delete_user", response_model=bool)
async def delete_user(
    # 使用 Body(..., embed=True) 可以让前端传递 {"user_id": 123} 格式的 JSON
    user_id: Annotated[int, Body(..., embed=True)],
    current_user: Annotated[UserIn, Depends(require_super_admin)],
):
    return await UserService.delete_user(user_id=user_id)


# 创建用户 (测试阶段取消权限限制)
@router.post("/create_user", response_model=UserOut)
async def create_user(
    user_data: Annotated[UserIn, Body(...)],
    # current_user: Annotated[UserIn, Depends()], # 如果测试不需要 token，可以暂时移除此依赖
):
    try:
        new_user = await UserService.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            level=UserLevel.REGULAR,
        )
    except Exception as E:
        print("当前错误: ", E)
        raise HTTPException(status_code=400, detail="用户创建失败")    
    
    if not new_user:
        raise HTTPException(status_code=400, detail="用户创建失败")
    return new_user