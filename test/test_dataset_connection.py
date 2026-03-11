import asyncio

import pytest
from tortoise import Tortoise, connections

from my_dataset import Config


async def _check_database_connection() -> None:
    config = Config()

    await Tortoise.init(config=config.load_db_config())
    try:
        connection = connections.get("default")
        row_count, rows = await connection.execute_query("SELECT 1 AS ok")

        assert row_count == 1
        assert rows[0]["ok"] == 1
    finally:
        await Tortoise.close_connections()


def test_dataset_connection() -> None:
    try:
        asyncio.run(_check_database_connection())
        print("数据库连接成功！")
    except Exception as exc:
        pytest.fail(f"数据库连接失败: {exc}")


if __name__ == "__main__":
    test_dataset_connection()

