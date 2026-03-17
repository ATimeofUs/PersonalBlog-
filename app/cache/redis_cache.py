import redis.asyncio as redis
import os
from typing import Literal
from pydantic import AnyUrl
from pydantic_settings import BaseSettings
from ..schemas import UserData, Token, PostDetail, CategoryDetail 

class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "dev")
    testing: str = os.getenv("TESTING", "0")
    redis_url: AnyUrl = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    redis_password: str = os.getenv("REDIS_PASSWORD", "redis_pass")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_hash: str = os.getenv("REDIS_TEST_KEY", "covid-19-test")
    up: str = os.getenv("UP", "up")
    down: str = os.getenv("DOWN", "down")
    web_server: str = os.getenv("WEB_SERVER", "web_server")

settings = Settings()

class RedisManager:
    def __init__(self):
        self.redis_client = None

    async def init_redis_pool(self):
        self.redis_client = await redis.from_url(
            settings.redis_url.unicode_string(),
            encoding="utf-8",
            db=settings.redis_db,
            decode_responses=True,
        )
        print(f"Connected to Redis at {settings.redis_url}")

    async def close_redis_pool(self):
        if self.redis_client:
            await self.redis_client.close()
            print("Redis connection closed")


    # user related methods
    async def set_user_status(self, user_id: int, status: Literal[0, 1]):
        """设置用户是否登录状态"""
        await self.redis_client.hset(settings.redis_hash, f"user:{user_id}", status)
    
    async def get_user_status(self, user_id: int) -> int:
        """获取用户状态，默认为 0（正常）"""
        status = await self.redis_client.hget(settings.redis_hash, f"user:{user_id}")
        return int(status) if status is not None else 0
    
    # post related methods
    
    # category related methods
    

redis_manager = RedisManager()

if __name__ == "__main__":
    import asyncio
    
    test_redis_manager = RedisManager()
    asyncio.run(test_redis_manager.init_redis_pool())
    print(f"Connected to Redis at {settings.redis_url}")