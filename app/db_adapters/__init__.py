#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库适配器模块
支持多种数据库类型的统一接口
"""

from .base import DatabaseAdapter
from .mysql_adapter import MySQLAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgresql_adapter import PostgreSQLAdapter

__all__ = [
    'DatabaseAdapter',
    'MySQLAdapter',
    'SQLiteAdapter',
    'PostgreSQLAdapter'
]


# 数据库类型常量
DB_TYPE_MYSQL = 'mysql'
DB_TYPE_SQLITE = 'sqlite'
DB_TYPE_POSTGRESQL = 'postgresql'

# 数据库类型显示名称
DB_TYPE_NAMES = {
    DB_TYPE_MYSQL: 'MySQL',
    DB_TYPE_SQLITE: 'SQLite',
    DB_TYPE_POSTGRESQL: 'PostgreSQL'
}

# 支持的数据库类型列表
SUPPORTED_DB_TYPES = [DB_TYPE_MYSQL, DB_TYPE_SQLITE, DB_TYPE_POSTGRESQL]


def get_adapter(db_type: str, config: dict) -> DatabaseAdapter:
    """
    根据数据库类型获取对应的适配器

    Args:
        db_type: 数据库类型 (mysql, sqlite, postgresql)
        config: 数据库配置

    Returns:
        数据库适配器实例

    Raises:
        ValueError: 不支持的数据库类型
    """
    adapters = {
        DB_TYPE_MYSQL: MySQLAdapter,
        DB_TYPE_SQLITE: SQLiteAdapter,
        DB_TYPE_POSTGRESQL: PostgreSQLAdapter
    }

    adapter_class = adapters.get(db_type.lower())
    if adapter_class is None:
        raise ValueError(f"不支持的数据库类型: {db_type}")

    return adapter_class(config)


def get_db_type_name(db_type: str) -> str:
    """获取数据库类型的显示名称"""
    return DB_TYPE_NAMES.get(db_type.lower(), db_type)


def is_supported_db_type(db_type: str) -> bool:
    """检查数据库类型是否支持"""
    return db_type.lower() in SUPPORTED_DB_TYPES
