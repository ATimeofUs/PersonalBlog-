from pathlib import Path
from uuid import uuid4

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


def is_supported_image(file_extension: str, file_header: bytes) -> bool:
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

        if not is_supported_image(file_extension, first_chunk):
            raise ValueError("图片内容与文件类型不匹配")

        with destination.open("wb") as file_obj:
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


def delete_avatar_file(avatar_path: str | None) -> None:
    if not avatar_path or not avatar_path.startswith(f"{AVATAR_URL_PREFIX}/"):
        return

    avatar_name = avatar_path.rsplit("/", 1)[-1]
    file_path = AVATAR_DIR / avatar_name
    if file_path.exists():
        file_path.unlink()