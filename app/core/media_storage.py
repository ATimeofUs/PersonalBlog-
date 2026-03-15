import os
import logging

from pathlib import Path
from uuid import uuid4
from ..models import ServiceError, User
from ..services import UserService
from fastapi import UploadFile


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEDIA_ROOT = PROJECT_ROOT / "media"
AVATAR_DIR = MEDIA_ROOT / "avatars"
AVATAR_URL_PREFIX = "/media/avatars"

_SIGNATURES = {
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),
}


async def is_supported_image(file_extension: str, file_header: bytes) -> bool:
    if file_extension == ".webp":
        return file_header.startswith(b"RIFF") and file_header[8:12] == b"WEBP"

    signatures = _SIGNATURES.get(file_extension, ())
    return any(file_header.startswith(signature) for signature in signatures)


async def save_avatar_file(
    upload_file: UploadFile,
    *,
    file_extension: str,
    max_size: int,
    read_chunk_size: int,
) -> str:
    """
    Args:
    - upload_file: 上传的文件对象
    - file_extension: 文件扩展名（如 .jpg）
    - max_size: 最大允许的文件大小（字节）
    - read_chunk_size: 读取文件的块大小（字节）

    Return:
    - 返回文件的名字

    Raise:
    - 返回报错
    """

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    # uuid4 生成唯一文件名，保留原始扩展名
    destination = AVATAR_DIR / f"{uuid4().hex}{file_extension}"
    total_read = 0

    try:
        first_chunk = await upload_file.read(read_chunk_size)
        if not first_chunk:
            raise ValueError("上传文件不能为空")

        if not await is_supported_image(file_extension, first_chunk):
            raise ValueError("图片内容与文件类型不匹配")

        # wb是二进制写入模式，适合图片等非文本文件
        with destination.open("wb") as file_obj:
            # 一块一块地写入文件，避免一次性加载大文件到内存
            chunk = first_chunk
            while chunk:
                total_read += len(chunk)
                if total_read > max_size:
                    raise ValueError("图片大小超过限制")

                file_obj.write(chunk)
                chunk = await upload_file.read(read_chunk_size)

        return f"{AVATAR_URL_PREFIX}/{destination.name}"
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    finally:
        await upload_file.close()


async def delete_avatar_file(avatar_path: str | None) -> None:
    if not avatar_path or not avatar_path.startswith(f"{AVATAR_URL_PREFIX}/"):
        return

    avatar_name = avatar_path.rsplit("/", 1)[-1]
    file_path = AVATAR_DIR / avatar_name
    
    logging.info("准备删除文件: %s", file_path)

    if file_path.exists():
        logging.info("已删除旧头像文件，真实文件位置: %s", file_path)
        file_path.unlink()
    else:
        logging.warning("旧头像文件不存在，无法删除: %s", file_path)    


async def update_profile_photo(
    user_id: int, profile_photo_path: str, old_photo_path: str | None
) -> User:
    """
    快速更新头像路径。

    Args:
        user_id (int): 用户 ID。
        profile_photo_path (str): 相对路径（通常由 media_storage 处理后传入）。
        old_photo_path (str | None): 旧头像路径，用于后续清理。
    """

    try:
        user = await UserService.update_profile_photo(
            user_id=user_id,
            profile_photo_path=profile_photo_path,
            old_photo_path=old_photo_path,
        )

        logging.info(
            "正在更新用户 %d 的头像，旧路径：%s，新路径：%s",
            user_id,
            old_photo_path,
            profile_photo_path,
        )
        
    except Exception as exc:
        logging.error("更新用户 %d 头像失败: %s", user_id, str(exc))
        raise ServiceError("头像更新失败")
    finally:
        logging.info("正在删除用户 %d 的旧头像文件，路径：%s", user_id, old_photo_path)
        await delete_avatar_file(old_photo_path)
        
    return user
