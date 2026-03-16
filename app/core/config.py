from dataclasses import dataclass
import os
import keyring
import ssl
from pathlib import Path


@dataclass
class TiDBConfig:
    DATASET_CONFIG = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "port": 4000,
                    "user": "3BoyLTN1Awt1r8H.root",
                    "database": "test",

                    "ssl": True,

                    # 连接池
                    "minsize": 5,
                    "maxsize": 20,

                    "charset": "utf8mb4"
                }
            }
        },
        "apps": {
            "models": {
                "models": [
                    "app.models.models",
                ],
                "default_connection": "default"
            }
        }
    }      


    def __init__(self):
        user_name = self.DATASET_CONFIG["connections"]["default"]["credentials"]["user"]
        password = keyring.get_password("tidb_service", user_name)
        host_name = keyring.get_password("tidb_service_host", user_name)
        
        self.DATASET_CONFIG["connections"]["default"]["credentials"]["host"] = host_name
        self.DATASET_CONFIG["connections"]["default"]["credentials"]["password"] = password
        self.DATASET_CONFIG["connections"]["default"]["credentials"]["ssl"] = self.create_ssl_context()
        

    def create_ssl_context(self) -> ssl.SSLContext:
        # 获取当前文件所在目录的绝对路径，方便定位 ASSETS 文件夹
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(BASE_DIR)  # 上一级目录
        BASE_DIR = os.path.dirname(BASE_DIR)  # 上一级目录
        
        ASSETS_DIR = "assets/pem"   
        
        # 创建 TLS 客户端上下文
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # 1. 加载 CA 证书 (验证 TiDB)
        ctx.load_verify_locations(
            cafile=os.path.join(ASSETS_DIR, "ca-cert.pem")
        )
        
        # 2. 加载客户端证书和私钥 (TiDB 验证你)
        ctx.load_cert_chain(
            certfile=os.path.join(ASSETS_DIR, "client-cert.pem"),
            keyfile=os.path.join(ASSETS_DIR, "client-key.pem")
        )
        
        # 3. 安全配置
        ctx.check_hostname = False  # 如果是用 IP 连接或者证书名不匹配，设为 False
        ctx.verify_mode = ssl.CERT_REQUIRED # 必须验证
        
        return ctx


    def load_db_config(self) -> dict:
        self.DATASET_CONFIG["connections"]["default"]["credentials"]["ssl"] = self.create_ssl_context()
        return self.DATASET_CONFIG

@dataclass
class SQLiteConfig:
    BASE_DIR = Path(__file__).parent.parent.parent
    DB_PATH = BASE_DIR / "assets" / "db" / "db.sqlite3"

    def load_db_config(self) -> dict:
        return {
            "connections": {
                "default": f"sqlite://{self.DB_PATH}"  # Tortoise 支持直接使用连接字符串
            },
            "apps": {
                "models": {
                    "models": ["app.models.models"],
                    "default_connection": "default",
                }
            },
            "use_tz": False,  # SQLite 对时区的支持较弱，建议设为 False 或统一使用 UTC
            "timezone": "UTC",
        }


    def load_memory_config(self) -> dict:
        return {
            "connections": {
                "default": "sqlite://:memory:"
            },
            "apps": {
                "models": {
                    "models": ["app.models.models"],
                    "default_connection": "default",
                }
            },
            "use_tz": False,  # SQLite 对时区的支持较弱，建议设为 False 或统一使用 UTC
            "timezone": "UTC",
        }

if __name__ == "__main__":
    config = SQLiteConfig()
    db_config = config.load_db_config()

    import rich
    rich.print(db_config)