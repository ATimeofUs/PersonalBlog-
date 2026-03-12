from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated

from ..services import UserService
from ..schemas.pydantic_model import Token
from ..core import create_access_token
    

# ========== 路径 ========== 
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    用户登录并生成访问令牌。
    参数：
        form_data (OAuth2PasswordRequestForm): 用户登录表单数据。
    返回：
        Token: 包含访问令牌和令牌类型的对象。
    异常：
        HTTPException: 如果用户名或密码错误。
    """
    
    user = await UserService.authenticate_user(
        form_data.username,
        form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": user.username})

    return Token(
        access_token=access_token,
        token_type="bearer",
    )
