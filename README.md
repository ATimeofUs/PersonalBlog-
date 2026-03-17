## 技术栈 / Built With

* [FastAPI](https://fastapi.tiangolo.com/) - Python Web 异步框架
* [Tortoise-ORM](https://tortoise.github.io/) - 异步 ORM
* [Pico CSS](https://picocss.com/) - Pico CSS 框架 (MIT License)
* [SQLlite](https://sqlite.org/) - 轻量级数据库
* [Redis](https://redis.io/) - 内存数据结构存储系统
* [Uvicorn](https://www.uvicorn.org/) - ASGI 服务器
* [Pytest](https://docs.pytest.org/) - Python 测试

## 运行环境
* **Python**: 3.11+
* **OS**: Arch Linux (开发) + Ubuntu (服务器)
* **Database**: SQLite 
* **Web Server**: Uvicorn (开发) + Gunicorn (生产)

## 项目结构


## 运行项目
1. 克隆仓库并进入项目目录：
```bash
git clone https://github.com/ATimeofUs/PersonalBlog-.git
cd PersonalBlog
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行：
```bash
uvicorn main:app --reload
```
也可以使用 

```bash
fastapi dev main.py
```

# 项目介绍：
## 1. app文件夹
- core 负责核心功能，如数据库配置，头像存储，oauth2认证等
- router 只负责接请求
- service 负责业务逻辑，对router暴露接口
- repo 只负责数据库, 对service暴露接口
- cache 只负责缓存, 对service暴露接口
## 2. test文件夹
- test_*.py 负责单元测试
- conftest.py 负责测试夹具，如测试数据库连接等
- locust_test_web 使用locaust工具进行压力测试
## 3. 其他文件
- main.py 入口文件，创建FastAPI实例并包含路由
- README.md 项目说明文档
- requirements.txt 依赖列表
- .gitignore Git忽略文件
