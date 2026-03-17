import random
import string
from locust import HttpUser, task, between

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class BlogUser(HttpUser):
    host = "http://127.0.0.1:8000"         # 根据实际服务情况修改，通常本地为http
    wait_time = between(1, 5)              # 模拟用户真实的阅读思考时间

    @task(5)   # 50% 流量
    def post_search(self):
        # 模拟前端加载文章列表
        self.client.get("/post/search?limit=10&offset=0")

    @task(3)   # 30% 流量
    def view_post(self):
        # 模拟访问首页
        self.client.get("/")

    @task(2)   # 20% 流量
    def category_search(self):
        # 模拟访问分类列表
        self.client.get("/category/list?limit=10&offset=0")

        
    @task(1)   # 10% 流量
    def create_user(self):
        # 模拟新用户注册，使用随机用户名防止重复报错
        username = f"locust_{random_string()}"
        self.client.post("/user/create", json={
            "username": username,
            "password": "Password123!",
            "email": f"{username}@example.com"
        })