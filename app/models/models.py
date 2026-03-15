from tortoise import fields
from tortoise.models import Model
from enum import IntEnum

# ============ 枚举定义 ============
class PostStatus(IntEnum):
    """文章状态枚举"""

    DRAFT = 0  # 草稿
    PUBLISHED = 1  # 已发布


class UserLevel(IntEnum):
    """用户等级枚举"""

    REGULAR = 0  # 普通用户
    ADMIN = 1  # 管理员
    SUPER_ADMIN = 2  # 超级管理员，就是我！


class Category(Model):
    """分类模型"""

    # 主键，并且自带自增功能
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True, description="分类名称")
    slug = fields.CharField(
        max_length=50, unique=True, description="分类别名（URL友好）"
    )
    description = fields.TextField(null=True, blank=True, description="分类描述")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(Model):
    """文章模型"""

    # 主键，并且自带自增功能
    id = fields.IntField(pk=True)

    # 基本信息
    title = fields.CharField(max_length=255, description="文章标题")
    slug = fields.CharField(
        max_length=255, unique=True, description="URL别名（用于SEO）"
    )
    excerpt = fields.TextField(null=True, blank=True, description="文章摘要")

    # 内容字段：只支持 Markdown
    content = fields.TextField(description="文章正文（Markdown 格式）")

    # 文章属性
    status = fields.IntField(
        default=PostStatus.DRAFT, description="发布状态: 0-草稿, 1-已发布"
    )
    is_featured = fields.BooleanField(default=False, description="是否为精选文章")

    # 浏览统计
    view_count = fields.IntField(default=0, description="浏览次数")

    # 关联字段
    # 外键关联：一个文章只能属于一个分类，但一个分类可以有多个文章
    category = fields.ForeignKeyField(
        "models.Category",
        related_name="posts",
        on_delete=fields.SET_NULL,
        null=True,
        description="所属分类",
    )

    # 外键关联：一个文章只能属于一个作者，但一个作者可以有多个文章
    author = fields.ForeignKeyField(
        "models.User",
        related_name="posts",
        on_delete=fields.CASCADE,
        description="文章作者",
    )


    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="最后更新时间")
    published_at = fields.DatetimeField(null=True, description="正式发布日期")

    class Meta:
        table = "posts"
        ordering = ["-published_at", "-created_at"]
        # 添加索引以提高查询性能
        indexes = [
            # 复合索引：分类和发布状态
            ("category", "status"),
            # 新增：作者和发布状态的复合索引
            ("author", "status"),
        ]

    def __str__(self):
        return self.title


class User(Model):
    """用户模型"""

    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    profile_photo = fields.CharField(max_length=255, null=True, blank=True, description="头像相对路径")
    email = fields.CharField(max_length=255, unique=True, description="邮箱地址")
    password_hash = fields.CharField(max_length=255, description="密码哈希值")
    level = fields.IntField(
        default=UserLevel.REGULAR,
        description="用户等级: 0-普通用户, 1-管理员, 2-超级管理员",
    )

    description = fields.TextField(max_length=1000, null=True, blank=True, description="用户简介")

    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "users"
        ordering = ["username"]

    def __str__(self):
        return self.username
    

async def main():
    from tortoise import Tortoise
    from app.core import SQLiteConfig

    config = SQLiteConfig()
    config = config.load_db_config()
    
    # 初始化 Tortoise ORM
    await Tortoise.init(config=config)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())