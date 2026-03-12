# PersonalBlog-
使用fastapi 和 tortoise orm搭建的个人博客平台

github地址：https://github.com/ATimeofUs/PersonalBlog-



## 数据库

使用的是TIDB，可以免费注册并且使用，使用tortoise初始化数据库的时候需要这样



```python
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()
register_tortoise(
	app,
	config= "你的config,
	generate_schemas=False, # 不自动生成数据库表结构，改为手动管理迁移
)
```





