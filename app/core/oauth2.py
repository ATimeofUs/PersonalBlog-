import keyring
import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from datetime import datetime, timedelta, timezone
from ..service import UserService
from ..schemas import UserData
from ..models import ServiceError

SECRET_KEY = keyring.get_password("auth_secret_key", "jwt") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 60 * 24 # 一天 

if SECRET_KEY is None:
    raise Exception("JWT secret key not found in keyring. Please set it using keyring.set_password('auth_secret_key', 'jwt', 'your_secret_key')")

def create_access_token(data: dict):
    """
    创建一个访问令牌。
    参数：
        data (dict): 包含用户信息的数据。
    返回：
        str: 编码后的 JWT 令牌。
    """
    to_encode = data.copy()
    
    # 终止日期为现 + access token expire minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # add to dict
    to_encode.update({"exp": expire})

    # 编码中
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


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},  
    )
    
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except jwt.ExpiredSignatureError:
        logging.info("Token 已过期")
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError as e:
        logging.warning("Token 校验失败: %s", e)
        raise credentials_exception

    try:
        user = await UserService.get_user_by_username(username=username)
    except ServiceError:
        raise credentials_exception

    return user

async def require_admin(current_user: Annotated[UserData, Depends(get_current_user)]):
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


async def require_super_admin(current_user: Annotated[UserData, Depends(get_current_user)]):
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