from .auth_router import router as auth_router
from .user_router import router as user_router
from .category_router import router as category_router
from .post_router import router as post_router

__all__ = [
    "auth_router",
    "user_router",
    "category_router",
    "post_router",
]