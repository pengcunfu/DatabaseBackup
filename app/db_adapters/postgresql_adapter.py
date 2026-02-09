#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库适配器
支持 PostgreSQL 9.x 及以上版本
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    sql = None
    RealDictCursor = None

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL 数据库适配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 PostgreSQL 适配器

        Args:
            config: 配置字典,包含:
                - host: 主机地址
                - port: 端口号
                - username: 用户名
                - password: 密码
                - database: 数据库名
        """
        if psycopg2 is None:
            raise ImportError("psycopg2 库未安装,请运行: pip install psycopg2-binary")

        super().__init__(config)

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return 'postgresql'

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=int(self.config.get('port', 5432)),
                user=self.config.get('username', 'postgres'),
                password=self.config.get('password', ''),
                database=self.config.get('database'),
                connect_timeout=10
            )
            self.connection.autocommit = False
            logger.info(f"PostgreSQL 连接成功: {self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL 连接失败: {e}")
            return False

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("PostgreSQL 连接已关闭")

    def get_table_list(self) -> List[str]:
        """获取数据库表列表"""
        try:
            cursor = self.connection.cursor()
            # 只获取当前 schema 中的表
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []

    def get_table_structure(self, table_name: str) -> str:
        """获取表结构(CREATE TABLE 语句)"""
        try:
            # PostgreSQL 没有直接的 SHOW CREATE TABLE,需要构建
            columns = self.get_table_columns(table_name)
            if not columns:
                return ""

            # 构建 CREATE TABLE 语句
            column_defs = []
            primary_keys = []

            for col in columns:
                col_def = f"\"{col['name']}\" {col['type']}"

                if not col['nullable']:
                    col_def += " NOT NULL"

                if col['default']:
                    col_def += f" DEFAULT {col['default']}"

                column_defs.append(col_def)

                if col['is_primary_key']:
                    primary_keys.append(f"\"{col['name']}\"")

            if primary_keys:
                column_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

            create_sql = f"CREATE TABLE \"{table_name}\" (\n    "
            create_sql += ",\n    ".join(column_defs)
            create_sql += "\n)"

            return create_sql
        except Exception as e:
            logger.error(f"获取表结构失败 {table_name}: {e}")
            return ""

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表字段信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    a.attname AS column_name,
                    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                    CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable,
                    COALESCE(pg_catalog.pg_get_expr(d.adbin, d.adrelid), '') AS default_value,
                    COALESCE(pg_catalog.pg_get_expr(d.adbin, d.adrelid) ~ 'nextval', FALSE) AS is_autoinc,
                    CASE WHEN pk.contype = 'p' THEN TRUE ELSE FALSE END AS is_primary_key
                FROM pg_attribute a
                LEFT JOIN pg_attrdef d ON (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
                LEFT JOIN pg_index i ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                LEFT JOIN pg_constraint pk ON i.indrelid = pk.conrelid AND i.indisprimary = pk.oid
                WHERE a.attrelid = '{}'::regclass
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                ORDER BY a.attnum
            """.format(table_name))

            rows = cursor.fetchall()
            cursor.close()

            columns = []
            for row in rows:
                # row: column_name, data_type, is_nullable, default_value, is_autoinc, is_primary_key
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3],
                    'is_primary_key': row[5],
                    'extra': 'auto_increment' if row[4] else ''
                })
            return columns
        except Exception as e:
            logger.error(f"获取表字段失败 {table_name}: {e}")
            return []

    def get_table_data(self, table_name: str, batch_size: int = 1000) -> List[tuple]:
        """获取表数据"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM \"{table_name}\"")
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            logger.error(f"获取表数据失败 {table_name}: {e}")
            return []

    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
            self.connection.commit()
            cursor.close()
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
            cursor.close()
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
            columns_str = ', '.join([f"\"{col}\"" for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO \"{table_name}\" ({columns_str}) VALUES ({placeholders})"

            # 批量插入
            cursor.executemany(sql, data)
            self.connection.commit()
            cursor.close()
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
            cursor.close()
            return True, "SQL执行成功"
        except Exception as e:
            self.connection.rollback()
            return False, f"SQL执行失败: {str(e)}"

    def begin_transaction(self) -> None:
        """开始事务"""
        if self.connection:
            self.connection.autocommit = False

    def commit(self) -> None:
        """提交事务"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """回滚事务"""
        if self.connection:
            self.connection.rollback()

    def quote_identifier(self, identifier: str) -> str:
        """给标识符添加双引号"""
        return f'"{identifier}"'

    def get_postgresql_version(self) -> str:
        """获取 PostgreSQL 版本"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            cursor.close()
            return version[0] if version else ""
        except Exception as e:
            logger.error(f"获取 PostgreSQL 版本失败: {e}")
            return ""

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
            sql_parts.append(f"DROP TABLE IF EXISTS \"{table_name}\";")
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
