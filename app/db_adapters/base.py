#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库适配器基类
定义所有数据库适配器必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库适配器

        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.connection = None
        self.db_type = self.get_db_type()

    @abstractmethod
    def get_db_type(self) -> str:
        """获取数据库类型标识"""
        pass

    @abstractmethod
    def connect(self) -> bool:
        """建立数据库连接"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    def get_table_list(self) -> List[str]:
        """获取数据库表列表"""
        pass

    @abstractmethod
    def get_table_structure(self, table_name: str) -> str:
        """获取表结构(CREATE TABLE语句)"""
        pass

    @abstractmethod
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表字段信息

        Returns:
            字段信息列表,每个字段包含: name, type, nullable, default, is_primary_key
        """
        pass

    @abstractmethod
    def get_table_data(self, table_name: str, batch_size: int = 1000) -> List[tuple]:
        """获取表数据"""
        pass

    @abstractmethod
    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        pass

    @abstractmethod
    def create_table(self, create_sql: str) -> bool:
        """创建表"""
        pass

    @abstractmethod
    def insert_data(self, table_name: str, columns: List[str], data: List[tuple]) -> bool:
        """批量插入数据"""
        pass

    @abstractmethod
    def execute_sql(self, sql: str) -> Tuple[bool, str]:
        """执行SQL语句"""
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """开始事务"""
        pass

    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass

    def format_value_for_sql(self, value: Any) -> str:
        """
        格式化值为SQL字面量

        Args:
            value: Python值

        Returns:
            SQL格式的字符串
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(value, bytes):
            return f"X'{value.hex()}'"
        else:
            # 转义字符串中的单引号
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def generate_insert_sql(self, table_name: str, columns: List[str], data: List[tuple]) -> str:
        """
        生成INSERT SQL语句

        Args:
            table_name: 表名
            columns: 字段名列表
            data: 数据列表

        Returns:
            INSERT SQL语句
        """
        if not data:
            return ''

        columns_str = ', '.join([self.quote_identifier(col) for col in columns])
        values_list = []

        for row in data:
            values = ', '.join([self.format_value_for_sql(val) for val in row])
            values_list.append(f"({values})")

        return f"INSERT INTO {self.quote_identifier(table_name)} ({columns_str}) VALUES\n" + ',\n'.join(values_list) + ';'

    @abstractmethod
    def quote_identifier(self, identifier: str) -> str:
        """
        给标识符(表名、字段名)添加引号

        Args:
            identifier: 标识符

        Returns:
            带引号的标识符
        """
        pass

    def test_connection(self) -> Tuple[bool, str]:
        """
        测试数据库连接

        Returns:
            (是否成功, 消息)
        """
        try:
            if self.connect():
                self.close()
                return True, "连接成功"
            else:
                return False, "连接失败"
        except Exception as e:
            return False, f"连接错误: {str(e)}"

    def __enter__(self):
        """支持上下文管理器"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.close()
