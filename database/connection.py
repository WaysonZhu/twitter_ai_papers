"""
数据库连接管理
"""
import logging
from contextlib import contextmanager
from typing import Generator

import pymysql
from pymysql.cursors import DictCursor

from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接管理器"""

    def __init__(self):
        self._config = settings.get_db_config()

    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        return pymysql.connect(
            **self._config,
            cursorclass=DictCursor,
            autocommit=False,
        )

    @contextmanager
    def connection(self) -> Generator[pymysql.Connection, None, None]:
        """上下文管理器，自动处理连接的获取和释放"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def cursor(self) -> Generator[pymysql.cursors.Cursor, None, None]:
        """上下文管理器，自动处理游标"""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()


# 全局数据库连接实例
db = DatabaseConnection()
