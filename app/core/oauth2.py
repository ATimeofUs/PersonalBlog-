import keyring
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from datetime import datetime, timedelta, timezone
from ..schemas import UserOut
from ..services import UserService

SECRET_KEY = keyring.get_password("auth_secret_key", "jwt") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def create_access_token(data: dict):
    """
    创建一个访问令牌。
    参数：
        data (dict): 包含用户信息的数据。
    返回：
        str: 编码后的 JWT 令牌。
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str):
    """
    解码访问令牌。
    参数：
        token (str): 编码的 JWT 令牌。
    返回：
        dict: 解码后的令牌数据。
    """
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )
    return payload


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    获取当前用户。
    参数：
        token (str): OAuth2 令牌。
    返回：
        UserOut: 当前用户对象。
    异常：
        HTTPException: 如果认证失败。
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = await UserService.get_user_by_username(username)

    if user is None:
        raise credentials_exception

    return user


async def require_admin(current_user: Annotated[UserOut, Depends(get_current_user)]):
    """
    验证用户是否具有管理员权限。
    参数：
        current_user (UserOut): 当前用户对象。
    返回：
        UserOut: 当前用户对象。
    异常：
        HTTPException: 如果用户权限不足。
    """
    if current_user.level < 1:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def require_super_admin(current_user: Annotated[UserOut, Depends(get_current_user)]):
    """
    验证用户是否具有超级管理员权限。
    参数：
        current_user (UserOut): 当前用户对象。
    返回：
        UserOut: 当前用户对象。
    异常：
        HTTPException: 如果用户权限不足。
    """
    if current_user.level < 2:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user

