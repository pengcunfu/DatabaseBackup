#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 数据库适配器
支持 SQLite 3.x 版本
"""

import logging
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

try:
    import sqlite3
except ImportError:
    sqlite3 = None

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 数据库适配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 SQLite 适配器

        Args:
            config: 配置字典,包含:
                - database: 数据库文件路径
        """
        if sqlite3 is None:
            raise ImportError("sqlite3 库不可用")

        super().__init__(config)

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return 'sqlite'

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            db_path = self.config.get('database', '')

            # 如果路径不存在,尝试创建目录
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row  # 返回字典格式

            logger.info(f"SQLite 连接成功: {db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite 连接失败: {e}")
            return False

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("SQLite 连接已关闭")

    def get_table_list(self) -> List[str]:
        """获取数据库表列表"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []

    def get_table_structure(self, table_name: str) -> str:
        """获取表结构"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"获取表结构失败 {table_name}: {e}")
            return ""

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表字段信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            rows = cursor.fetchall()

            columns = []
            for row in rows:
                # row: (cid, name, type, notnull, default_value, pk)
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'nullable': not row[3],
                    'default': row[4],
                    'is_primary_key': row[5] > 0,
                    'extra': ''
                })
            return columns
        except Exception as e:
            logger.error(f"获取表字段失败 {table_name}: {e}")
            return []

    def get_table_data(self, table_name: str, batch_size: int = 1000) -> List[tuple]:
        """获取表数据"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM `{table_name}`")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取表数据失败 {table_name}: {e}")
            return []

    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            self.connection.commit()
            logger.info(f"表已删除: {table_name}")
            return True
        except Exception as e:
            logger.error(f"删除表失败 {table_name}: {e}")
            self.connection.rollback()
            return False

    def create_table(self, create_sql: str) -> bool:
        """创建表"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_sql)
            self.connection.commit()
            logger.info("表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            self.connection.rollback()
            return False

    def insert_data(self, table_name: str, columns: List[str], data: List[tuple]) -> bool:
        """批量插入数据"""
        if not data:
            return True

        try:
            cursor = self.connection.cursor()

            # 构建INSERT SQL
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join([f'`{col}`' for col in columns])
            sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

            # 批量插入
            cursor.executemany(sql, data)
            self.connection.commit()
            logger.info(f"插入 {len(data)} 条数据到 {table_name}")
            return True
        except Exception as e:
            logger.error(f"插入数据失败 {table_name}: {e}")
            self.connection.rollback()
            return False

    def execute_sql(self, sql: str) -> Tuple[bool, str]:
        """执行SQL语句"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()
            return True, "SQL执行成功"
        except Exception as e:
            self.connection.rollback()
            return False, f"SQL执行失败: {str(e)}"

    def begin_transaction(self) -> None:
        """开始事务"""
        if self.connection:
            self.connection.execute("BEGIN")

    def commit(self) -> None:
        """提交事务"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """回滚事务"""
        if self.connection:
            self.connection.rollback()

    def quote_identifier(self, identifier: str) -> str:
        """给标识符添加引号"""
        # SQLite 使用双引号或方括号,但这里使用反引号也能工作
        return f"`{identifier}`"

    def export_table_sql(self, table_name: str, include_data: bool = True) -> str:
        """
        导出表为 SQL (兼容 MySQL 格式)

        Args:
            table_name: 表名
            include_data: 是否包含数据

        Returns:
            SQL 语句
        """
        sql_parts = []

        # 表结构
        create_sql = self.get_table_structure(table_name)
        if create_sql:
            sql_parts.append(f"-- 表结构: {table_name}")
            sql_parts.append(f"DROP TABLE IF EXISTS `{table_name}`;")
            sql_parts.append(f"{create_sql};\n")

        # 表数据
        if include_data:
            columns = self.get_table_columns(table_name)
            if columns:
                column_names = [col['name'] for col in columns]
                data = self.get_table_data(table_name)

                if data:
                    sql_parts.append(f"-- 表数据: {table_name}")

                    # 分批处理,每批 500 条
                    batch_size = 500
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i+batch_size]
                        insert_sql = self.generate_insert_sql(table_name, column_names, batch)
                        sql_parts.append(insert_sql)
                        sql_parts.append("")

        return '\n'.join(sql_parts)

    def get_sqlite_version(self) -> str:
        """获取 SQLite 版本"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            return version[0] if version else ""
        except Exception as e:
            logger.error(f"获取 SQLite 版本失败: {e}")
            return ""
