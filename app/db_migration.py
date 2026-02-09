#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移模块
支持多种数据库之间的数据迁移
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from .db_adapters import get_adapter, SUPPORTED_DB_TYPES
from .db_adapters.type_mapping import DataTypeMapper

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """数据库迁移类 - 支持多数据库之间的迁移"""

    def __init__(self, source_config: Dict[str, Any], target_config: Dict[str, Any]):
        """
        初始化数据库迁移

        Args:
            source_config: 源数据库配置
            target_config: 目标数据库配置
        """
        self.source_config = source_config
        self.target_config = target_config
        self.source_adapter = None
        self.target_adapter = None

    def connect(self) -> bool:
        """连接源数据库和目标数据库"""
        try:
            # 获取数据库类型
            source_db_type = self.source_config.get('db_type', 'mysql')
            target_db_type = self.target_config.get('db_type', 'mysql')

            logger.info(f"源数据库类型: {source_db_type}")
            logger.info(f"目标数据库类型: {target_db_type}")

            # 创建适配器
            self.source_adapter = get_adapter(source_db_type, self.source_config)
            self.target_adapter = get_adapter(target_db_type, self.target_config)

            # 连接数据库
            if not self.source_adapter.connect():
                logger.error("源数据库连接失败")
                return False

            if not self.target_adapter.connect():
                logger.error("目标数据库连接失败")
                return False

            logger.info("数据库连接成功")
            return True

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def close(self) -> None:
        """关闭数据库连接"""
        if self.source_adapter:
            self.source_adapter.close()
        if self.target_adapter:
            self.target_adapter.close()

    def migrate_table(self, table_name: str, drop_target: bool = True,
                      convert_types: bool = True) -> bool:
        """
        迁移单个表

        Args:
            table_name: 表名
            drop_target: 是否删除目标表
            convert_types: 是否转换数据类型

        Returns:
            是否成功
        """
        logger.info(f"开始迁移表: {table_name}")

        try:
            # 获取源表结构
            create_sql = self.source_adapter.get_table_structure(table_name)
            if not create_sql:
                logger.error(f"无法获取表结构: {table_name}")
                return False

            # 转换表结构SQL
            if convert_types:
                source_db_type = self.source_config.get('db_type', 'mysql')
                target_db_type = self.target_config.get('db_type', 'mysql')
                create_sql = DataTypeMapper.convert_create_table_sql(
                    create_sql, source_db_type, target_db_type
                )

            # 删除目标表(如果需要)
            if drop_target:
                if not self.target_adapter.drop_table(table_name):
                    logger.warning(f"删除目标表失败或表不存在: {table_name}")

            # 创建目标表
            if not self.target_adapter.create_table(create_sql):
                logger.error(f"创建目标表失败: {table_name}")
                return False

            # 获取源表数据
            data = self.source_adapter.get_table_data(table_name)
            if not data:
                logger.info(f"表 {table_name} 无数据,跳过数据迁移")
                return True

            # 获取源表字段
            columns_info = self.source_adapter.get_table_columns(table_name)
            if not columns_info:
                logger.error(f"无法获取表字段: {table_name}")
                return False

            columns = [col['name'] for col in columns_info]

            # 插入数据到目标表
            if not self.target_adapter.insert_data(table_name, columns, data):
                logger.error(f"插入数据失败: {table_name}")
                return False

            logger.info(f"表 {table_name} 迁移完成,共迁移 {len(data)} 条记录")
            return True

        except Exception as e:
            logger.error(f"迁移表失败 {table_name}: {e}")
            return False

    def migrate_database(self, exclude_tables: List[str] = None,
                         include_tables: List[str] = None,
                         drop_target_tables: bool = True,
                         convert_types: bool = True,
                         progress_callback=None) -> bool:
        """
        迁移整个数据库

        Args:
            exclude_tables: 要排除的表列表
            include_tables: 要包含的表列表(如果指定,则只迁移这些表)
            drop_target_tables: 是否删除目标表
            convert_types: 是否转换数据类型
            progress_callback: 进度回调函数

        Returns:
            是否全部成功
        """
        if exclude_tables is None:
            exclude_tables = []

        # 获取源数据库表列表
        source_tables = self.source_adapter.get_table_list()
        if not source_tables:
            logger.error("源数据库无表或获取表列表失败")
            return False

        # 过滤表列表
        tables_to_migrate = []
        for table in source_tables:
            if table in exclude_tables:
                logger.info(f"跳过表: {table} (在排除列表中)")
                continue

            if include_tables and table not in include_tables:
                logger.info(f"跳过表: {table} (不在包含列表中)")
                continue

            tables_to_migrate.append(table)

        logger.info(f"准备迁移 {len(tables_to_migrate)} 个表: {', '.join(tables_to_migrate)}")

        # 迁移表
        success_count = 0
        total_tables = len(tables_to_migrate)

        for i, table in enumerate(tables_to_migrate):
            # 报告进度
            progress = int((i / total_tables) * 100)
            logger.info(f"进度: {progress}% - 正在迁移表 {i+1}/{total_tables}: {table}")

            if progress_callback:
                progress_callback(progress, f"正在迁移表: {table}")

            if self.migrate_table(table, drop_target_tables, convert_types):
                success_count += 1
            else:
                logger.error(f"表 {table} 迁移失败")

        # 最终进度更新
        logger.info(f"进度: 100% - 迁移完成")
        if progress_callback:
            progress_callback(100, "迁移完成")

        logger.info(f"迁移完成: {success_count}/{total_tables} 个表迁移成功")
        return success_count == total_tables

    def export_database(self, output_path: str,
                       exclude_tables: List[str] = None,
                       include_tables: List[str] = None,
                       include_data: bool = True,
                       progress_callback=None) -> bool:
        """
        导出数据库为 SQL 文件

        Args:
            output_path: 输出文件路径
            exclude_tables: 要排除的表列表
            include_tables: 要包含的表列表
            include_data: 是否包含数据
            progress_callback: 进度回调函数

        Returns:
            是否成功
        """
        if exclude_tables is None:
            exclude_tables = []

        # 获取源数据库表列表
        tables = self.source_adapter.get_table_list()
        if not tables:
            logger.error("数据库无表或获取表列表失败")
            return False

        # 过滤表列表
        tables_to_export = []
        for table in tables:
            if table in exclude_tables:
                logger.info(f"跳过表: {table} (在排除列表中)")
                continue

            if include_tables and table not in include_tables:
                logger.info(f"跳过表: {table} (不在包含列表中)")
                continue

            tables_to_export.append(table)

        logger.info(f"准备导出 {len(tables_to_export)} 个表: {', '.join(tables_to_export)}")

        # 创建输出目录
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 打开输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头信息
            f.write(f"-- 数据库导出\n")
            f.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 源数据库: {self.source_config.get('database')}\n")
            f.write(f"-- 源数据库类型: {self.source_config.get('db_type', 'mysql')}\n\n")

            # 导出所有表
            success_count = 0
            total_tables = len(tables_to_export)

            for i, table in enumerate(tables_to_export):
                # 报告进度
                progress = int((i / total_tables) * 100)
                logger.info(f"进度: {progress}% - 正在导出表 {i+1}/{total_tables}: {table}")

                if progress_callback:
                    progress_callback(progress, f"正在导出表: {table}")

                # 导出表
                if hasattr(self.source_adapter, 'export_table_sql'):
                    sql = self.source_adapter.export_table_sql(table, include_data)
                    if sql:
                        f.write(sql + "\n\n")
                        success_count += 1
                    else:
                        logger.error(f"表 {table} 导出失败")
                else:
                    logger.error(f"适配器不支持导出功能")

        # 最终进度更新
        logger.info(f"进度: 100% - 导出完成")
        if progress_callback:
            progress_callback(100, "导出完成")

        logger.info(f"SQL导出完成: {output_path}")
        logger.info(f"共导出 {success_count}/{total_tables} 个表")
        return success_count == total_tables

    def import_database(self, sql_file_path: str,
                       progress_callback=None) -> Tuple[bool, List[str]]:
        """
        导入 SQL 文件

        Args:
            sql_file_path: SQL 文件路径
            progress_callback: 进度回调函数

        Returns:
            (是否成功, 错误列表)
        """
        try:
            # 读取SQL文件
            logger.info(f"读取SQL文件: {sql_file_path}")

            # 转换SQL语法(如果需要)
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 如果源和目标数据库类型不同,需要转换SQL
            # 这里简化处理,直接执行
            success, errors = self._execute_sql_script(sql_content, progress_callback)

            if success:
                logger.info("SQL导入成功")
            else:
                logger.warning(f"SQL导入部分完成: {len(errors)} 个错误")

            return success, errors

        except Exception as e:
            logger.error(f"SQL导入失败: {e}")
            return False, [str(e)]

    def _execute_sql_script(self, sql_content: str,
                           progress_callback=None) -> Tuple[bool, List[str]]:
        """执行SQL脚本"""
        errors = []

        # 分割SQL语句(以分号结尾)
        sql_statements = []
        current_statement = ""
        in_delimiter = False

        for line in sql_content.splitlines():
            stripped_line = line.strip()

            # 跳过注释行
            if stripped_line.startswith('--') or stripped_line.startswith('#'):
                continue

            # 处理 DELIMITER 命令(MySQL)
            if stripped_line.upper().startswith('DELIMITER'):
                in_delimiter = True
                continue

            current_statement += line + " "

            if stripped_line.endswith(';') and not in_delimiter:
                sql_statements.append(current_statement.strip())
                current_statement = ""

        # 添加最后一个语句
        if current_statement.strip():
            sql_statements.append(current_statement.strip())

        logger.info(f"共解析 {len(sql_statements)} 条SQL语句")

        # 执行SQL语句
        success_count = 0
        total_statements = len(sql_statements)

        for i, statement in enumerate(sql_statements):
            if not statement.strip():
                continue

            try:
                success, msg = self.target_adapter.execute_sql(statement)
                if success:
                    success_count += 1
                else:
                    errors.append(msg)

                # 定期报告进度
                if (i + 1) % 100 == 0 or (i + 1) == total_statements:
                    progress = int(((i + 1) / total_statements) * 100)
                    logger.info(f"进度: {progress}% - 已执行 {i + 1}/{total_statements} 条SQL语句")
                    if progress_callback:
                        progress_callback(progress, f"已执行 {i + 1}/{total_statements} 条SQL语句")

            except Exception as e:
                errors.append(f"语句 {i + 1}: {str(e)}")
                logger.error(f"SQL执行错误 (语句 {i + 1}): {str(e)}")

        if errors:
            logger.warning(f"SQL执行部分成功: {success_count}/{total_statements} 条语句执行成功")
            return False, errors
        else:
            logger.info(f"SQL执行成功: {success_count}/{total_statements} 条语句执行成功")
            return True, []
