#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库类型映射和转换
支持不同数据库之间的数据类型转换
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DataTypeMapper:
    """数据类型映射器"""

    # MySQL 到其他数据库的类型映射
    MYSQL_TO_SQLITE = {
        # 整数类型
        'TINYINT': 'INTEGER',
        'SMALLINT': 'INTEGER',
        'MEDIUMINT': 'INTEGER',
        'INT': 'INTEGER',
        'INTEGER': 'INTEGER',
        'BIGINT': 'INTEGER',

        # 浮点类型
        'FLOAT': 'REAL',
        'DOUBLE': 'REAL',
        'DECIMAL': 'REAL',
        'NUMERIC': 'REAL',

        # 字符串类型
        'CHAR': 'TEXT',
        'VARCHAR': 'TEXT',
        'TINYTEXT': 'TEXT',
        'TEXT': 'TEXT',
        'MEDIUMTEXT': 'TEXT',
        'LONGTEXT': 'TEXT',

        # 二进制类型
        'TINYBLOB': 'BLOB',
        'BLOB': 'BLOB',
        'MEDIUMBLOB': 'BLOB',
        'LONGBLOB': 'BLOB',
        'BINARY': 'BLOB',
        'VARBINARY': 'BLOB',

        # 日期时间类型
        'DATE': 'TEXT',
        'TIME': 'TEXT',
        'DATETIME': 'TEXT',
        'TIMESTAMP': 'TEXT',
        'YEAR': 'INTEGER',

        # 布尔类型
        'BOOL': 'INTEGER',
        'BOOLEAN': 'INTEGER',

        # 其他
        'ENUM': 'TEXT',
        'SET': 'TEXT',
        'JSON': 'TEXT',
    }

    MYSQL_TO_POSTGRESQL = {
        # 整数类型
        'TINYINT': 'SMALLINT',
        'SMALLINT': 'SMALLINT',
        'MEDIUMINT': 'INTEGER',
        'INT': 'INTEGER',
        'INTEGER': 'INTEGER',
        'BIGINT': 'BIGINT',

        # 浮点类型
        'FLOAT': 'REAL',
        'DOUBLE': 'DOUBLE PRECISION',
        'DECIMAL': 'NUMERIC',
        'NUMERIC': 'NUMERIC',

        # 字符串类型
        'CHAR': 'CHARACTER',
        'VARCHAR': 'VARCHAR',
        'TINYTEXT': 'TEXT',
        'TEXT': 'TEXT',
        'MEDIUMTEXT': 'TEXT',
        'LONGTEXT': 'TEXT',

        # 二进制类型
        'TINYBLOB': 'BYTEA',
        'BLOB': 'BYTEA',
        'MEDIUMBLOB': 'BYTEA',
        'LONGBLOB': 'BYTEA',
        'BINARY': 'BYTEA',
        'VARBINARY': 'BYTEA',

        # 日期时间类型
        'DATE': 'DATE',
        'TIME': 'TIME',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP',
        'YEAR': 'INTEGER',

        # 布尔类型
        'BOOL': 'BOOLEAN',
        'BOOLEAN': 'BOOLEAN',

        # 其他
        'ENUM': 'VARCHAR',  # PostgreSQL 没有 ENUM,转为 VARCHAR
        'SET': 'TEXT',
        'JSON': 'JSONB',
    }

    # SQLite 到其他数据库的类型映射
    SQLITE_TO_MYSQL = {
        'INTEGER': 'INT',
        'REAL': 'DOUBLE',
        'TEXT': 'TEXT',
        'BLOB': 'BLOB',
        'NUMERIC': 'DECIMAL',
    }

    SQLITE_TO_POSTGRESQL = {
        'INTEGER': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'NUMERIC': 'NUMERIC',
    }

    # PostgreSQL 到其他数据库的类型映射
    POSTGRESQL_TO_MYSQL = {
        'SMALLINT': 'SMALLINT',
        'INTEGER': 'INT',
        'BIGINT': 'BIGINT',
        'DECIMAL': 'DECIMAL',
        'NUMERIC': 'DECIMAL',
        'REAL': 'DOUBLE',
        'DOUBLE PRECISION': 'DOUBLE',
        'CHARACTER': 'CHAR',
        'VARCHAR': 'VARCHAR',
        'TEXT': 'TEXT',
        'BYTEA': 'BLOB',
        'DATE': 'DATE',
        'TIME': 'TIME',
        'TIMESTAMP': 'DATETIME',
        'BOOLEAN': 'TINYINT',
        'JSONB': 'JSON',
        'JSON': 'JSON',
    }

    POSTGRESQL_TO_SQLITE = {
        'SMALLINT': 'INTEGER',
        'INTEGER': 'INTEGER',
        'BIGINT': 'INTEGER',
        'DECIMAL': 'REAL',
        'NUMERIC': 'REAL',
        'REAL': 'REAL',
        'DOUBLE PRECISION': 'REAL',
        'CHARACTER': 'TEXT',
        'VARCHAR': 'TEXT',
        'TEXT': 'TEXT',
        'BYTEA': 'BLOB',
        'DATE': 'TEXT',
        'TIME': 'TEXT',
        'TIMESTAMP': 'TEXT',
        'BOOLEAN': 'INTEGER',
        'JSONB': 'TEXT',
        'JSON': 'TEXT',
    }

    @classmethod
    def map_type(cls, source_type: str, source_db: str, target_db: str) -> str:
        """
        映射数据类型

        Args:
            source_type: 源数据库类型
            source_db: 源数据库类型 (mysql, sqlite, postgresql)
            target_db: 目标数据库类型 (mysql, sqlite, postgresql)

        Returns:
            目标数据库类型
        """
        # 提取基础类型(去掉长度等修饰符)
        base_type = source_type.upper().split('(')[0].strip()

        # 如果源和目标数据库类型相同,直接返回
        if source_db == target_db:
            return source_type

        # 构建映射表名称
        mapping_name = f"{source_db.upper()}_TO_{target_db.upper()}"

        # 获取对应的映射表
        mapping = getattr(cls, mapping_name, {})

        # 查找映射
        target_type = mapping.get(base_type)

        if target_type is None:
            logger.warning(f"未找到类型映射: {source_db}.{base_type} -> {target_db},使用原类型")
            return source_type

        # 保留原类型的长度信息(如果有)
        if '(' in source_type:
            # 提取长度信息
            length_part = source_type[source_type.index('('):]
            # 某些类型不支持长度,需要去掉
            if target_type not in ['TEXT', 'BLOB', 'BYTEA', 'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'BOOLEAN', 'JSON', 'JSONB']:
                return f"{target_type}{length_part}"

        return target_type

    @classmethod
    def convert_create_table_sql(cls, create_sql: str, source_db: str, target_db: str,
                                 source_identifier_quote: str = '`',
                                 target_identifier_quote: str = '`') -> str:
        """
        转换 CREATE TABLE SQL 语句

        Args:
            create_sql: 源 CREATE TABLE 语句
            source_db: 源数据库类型
            target_db: 目标数据库类型
            source_identifier_quote: 源数据库标识符引号
            target_identifier_quote: 目标数据库标识符引号

        Returns:
            转换后的 CREATE TABLE 语句
        """
        import re

        result = create_sql

        # 替换标识符引号
        if source_identifier_quote != target_identifier_quote:
            result = result.replace(source_identifier_quote, target_identifier_quote)

        # 转换数据类型
        # 匹配数据类型的正则表达式
        type_pattern = r'\b([A-Z]+)(?:\([^)]*\))?'

        def replace_type(match):
            source_type = match.group(0)
            base_type = match.group(1)
            mapped_type = cls.map_type(source_type, source_db, target_db)

            # 如果原类型有长度修饰,尝试保留
            if '(' in source_type and mapped_type == base_type:
                return source_type
            return mapped_type

        result = re.sub(type_pattern, replace_type, result, flags=re.IGNORECASE)

        # 处理特定数据库的语法差异
        result = cls._handle_syntax_differences(result, source_db, target_db)

        return result

    @classmethod
    def _handle_syntax_differences(cls, sql: str, source_db: str, target_db: str) -> str:
        """
        处理不同数据库的语法差异

        Args:
            sql: SQL 语句
            source_db: 源数据库类型
            target_db: 目标数据库类型

        Returns:
            处理后的 SQL 语句
        """
        result = sql

        # MySQL 特定语法转换
        if source_db == 'mysql':
            if target_db == 'sqlite':
                # 移除 MySQL 特定的 ENGINE 选项
                result = re.sub(r'\s*ENGINE\s*=\s*\w+', '', result, flags=re.IGNORECASE)
                result = re.sub(r'\s*DEFAULT\s+CHARSET\s*=\s*\w+', '', result, flags=re.IGNORECASE)
                result = re.sub(r'\s*COLLATE\s*=\s*\w+', '', result, flags=re.IGNORECASE)
                # 移除 AUTO_INCREMENT
                result = re.sub(r'\s*AUTO_INCREMENT\s*=\s*\d+', '', result, flags=re.IGNORECASE)

            elif target_db == 'postgresql':
                # ENGINE 转换为 USING (对于索引)
                # 移除 AUTO_INCREMENT
                result = re.sub(r'\s*AUTO_INCREMENT\s*=\s*\d+', '', result, flags=re.IGNORECASE)

        # SQLite 特定语法转换
        elif source_db == 'sqlite':
            if target_db == 'mysql':
                # SQLite 的 AUTOINCREMENT 需要转换为 AUTO_INCREMENT
                result = result.replace('AUTOINCREMENT', 'AUTO_INCREMENT')

        # PostgreSQL 特定语法转换
        elif source_db == 'postgresql':
            if target_db == 'mysql':
                # PostgreSQL 的 SERIAL 需要转换为 AUTO_INCREMENT
                result = re.sub(r'\bSERIAL\b', 'INT AUTO_INCREMENT', result, flags=re.IGNORECASE)
                result = re.sub(r'\bBIGSERIAL\b', 'BIGINT AUTO_INCREMENT', result, flags=re.IGNORECASE)

        return result

    @classmethod
    def get_compatible_type(cls, types: List[str], source_db: str, target_db: str) -> List[str]:
        """
        获取兼容的类型列表

        Args:
            types: 类型列表
            source_db: 源数据库类型
            target_db: 目标数据库类型

        Returns:
            映射后的类型列表
        """
        return [cls.map_type(t, source_db, target_db) for t in types]


# 便捷函数
def map_data_type(source_type: str, source_db: str, target_db: str) -> str:
    """映射数据类型"""
    return DataTypeMapper.map_type(source_type, source_db, target_db)


def convert_sql_syntax(sql: str, source_db: str, target_db: str) -> str:
    """转换 SQL 语法"""
    return DataTypeMapper.convert_create_table_sql(sql, source_db, target_db)
