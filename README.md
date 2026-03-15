## 技术栈 / Built With

* [FastAPI](https://fastapi.tiangolo.com/) - Python Web 异步框架
* [Tortoise-ORM](https://tortoise.github.io/) - 异步 ORM
* [Pico CSS](https://picocss.com/) - Pico CSS 框架 (MIT License)
* [SQLlite](https://sqlite.org/) - 轻量级数据库

## 运行环境
* **Python**: 3.11+
* **OS**: Arch Linux (Tested) + Ubuntu (服务器)
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