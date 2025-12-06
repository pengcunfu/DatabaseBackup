#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具 - 同步模块
数据库同步、导出和SQL执行的核心功能
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Any

try:
    import pymysql
except ImportError:
    print("错误: PyMySQL库未安装")
    print("安装命令: pip install pymysql")
    sys.exit(1)

from .db_config import DatabaseConfig

# 获取日志记录器（不重复配置）
logger = logging.getLogger(__name__)

class DatabaseSynchronizer:
    """数据库同步类"""
    
    def __init__(self, source_config: DatabaseConfig, target_config: DatabaseConfig = None):
        self.source_config = source_config
        self.target_config = target_config
        self.source_conn = None
        self.target_conn = None
    
    def connect_databases(self) -> bool:
        """连接源数据库和目标数据库"""
        if not self.target_config:
            logger.error("未提供目标数据库配置")
            return False
        
        try:
            # 连接源数据库
            logger.info(f"正在连接源数据库: {self.source_config.host}:{self.source_config.port}")
            self.source_conn = pymysql.connect(
                host=self.source_config.host,
                port=self.source_config.port,
                user=self.source_config.user,
                password=self.source_config.password,
                database=self.source_config.database,
                charset='utf8mb4',
                autocommit=False
            )
            logger.info("源数据库连接成功")
            
            # 连接目标数据库
            logger.info(f"正在连接目标数据库: {self.target_config.host}:{self.target_config.port}")
            self.target_conn = pymysql.connect(
                host=self.target_config.host,
                port=self.target_config.port,
                user=self.target_config.user,
                password=self.target_config.password,
                database=self.target_config.database,
                charset='utf8mb4',
                autocommit=False
            )
            logger.info("目标数据库连接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def connect_single_database(self, config: DatabaseConfig) -> Optional[pymysql.connections.Connection]:
        """连接单个数据库"""
        try:
            logger.info(f"正在连接数据库: {config.host}:{config.port}/{config.database}")
            conn = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                charset='utf8mb4',
                autocommit=False
            )
            logger.info("数据库连接成功")
            return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return None
    
    def get_table_list(self, connection) -> List[str]:
        """获取数据库表列表"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        except Exception as e:
            logger.error(f"获取表列表失败: {str(e)}")
            return []
    
    def get_table_structure(self, connection, table_name: str) -> str:
        """获取表结构"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                result = cursor.fetchone()
                return result[1] if result else ""
        except Exception as e:
            logger.error(f"获取表结构失败 {table_name}: {str(e)}")
            return ""
    
    def get_table_data(self, connection, table_name: str) -> List[tuple]:
        """获取表数据"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `{table_name}`")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取表数据失败 {table_name}: {str(e)}")
            return []
    
    def get_table_columns(self, connection, table_name: str) -> List[str]:
        """获取表字段列表"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [row[0] for row in cursor.fetchall()]
                return columns
        except Exception as e:
            logger.error(f"获取表字段失败 {table_name}: {str(e)}")
            return []
    
    def drop_table_if_exists(self, connection, table_name: str) -> bool:
        """删除表（如果存在）"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                connection.commit()
                return True
        except Exception as e:
            logger.error(f"删除表失败 {table_name}: {str(e)}")
            return False
    
    def create_table(self, connection, create_sql: str) -> bool:
        """创建表"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_sql)
                connection.commit()
                return True
        except Exception as e:
            logger.error(f"创建表失败: {str(e)}")
            return False
    
    def insert_data(self, connection, table_name: str, columns: List[str], data: List[tuple]) -> bool:
        """插入数据到表中"""
        if not data:
            return True
            
        try:
            with connection.cursor() as cursor:
                # 构建INSERT SQL
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join([f'`{col}`' for col in columns])
                sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
                
                # 批量插入
                cursor.executemany(sql, data)
                connection.commit()
                return True
        except Exception as e:
            logger.error(f"插入数据失败 {table_name}: {str(e)}")
            connection.rollback()
            return False
    
    def sync_table(self, table_name: str, drop_target: bool = True) -> bool:
        """同步单个表"""
        logger.info(f"开始同步表: {table_name}")
        
        try:
            # 获取源表结构
            create_sql = self.get_table_structure(self.source_conn, table_name)
            if not create_sql:
                logger.error(f"无法获取表结构: {table_name}")
                return False
            
            # 删除目标表（如果需要）
            if drop_target:
                if not self.drop_table_if_exists(self.target_conn, table_name):
                    logger.error(f"删除目标表失败: {table_name}")
                    return False
            
            # 创建目标表
            if not self.create_table(self.target_conn, create_sql):
                logger.error(f"创建目标表失败: {table_name}")
                return False
            
            # 获取源表数据
            data = self.get_table_data(self.source_conn, table_name)
            if not data:
                logger.info(f"表 {table_name} 无数据，跳过数据同步")
                return True
            
            # 获取表字段
            columns = self.get_table_columns(self.source_conn, table_name)
            if not columns:
                logger.error(f"无法获取表字段: {table_name}")
                return False
            
            # 插入数据到目标表
            if not self.insert_data(self.target_conn, table_name, columns, data):
                logger.error(f"插入数据失败: {table_name}")
                return False
            
            logger.info(f"表 {table_name} 同步完成，共同步 {len(data)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"同步表失败 {table_name}: {str(e)}")
            return False
    
    def sync_all_tables(self, exclude_tables: List[str] = None, include_tables: List[str] = None) -> bool:
        """同步所有表"""
        if exclude_tables is None:
            exclude_tables = []
        
        # 获取源数据库表列表
        source_tables = self.get_table_list(self.source_conn)
        if not source_tables:
            logger.error("源数据库无表或获取表列表失败")
            return False
        
        # 过滤表列表
        tables_to_sync = []
        for table in source_tables:
            if table in exclude_tables:
                logger.info(f"跳过表: {table} (在排除列表中)")
                continue
            
            if include_tables and table not in include_tables:
                logger.info(f"跳过表: {table} (不在包含列表中)")
                continue
            
            tables_to_sync.append(table)
        
        logger.info(f"准备同步 {len(tables_to_sync)} 个表: {', '.join(tables_to_sync)}")
        
        # 同步表
        success_count = 0
        total_tables = len(tables_to_sync)
        
        for i, table in enumerate(tables_to_sync):
            # 报告进度
            progress = int((i / total_tables) * 100)
            logger.info(f"进度: {progress}% - 正在同步表 {i+1}/{total_tables}: {table}")
            
            if self.sync_table(table):
                success_count += 1
            else:
                logger.error(f"表 {table} 同步失败")
        
        # 最终进度更新
        logger.info(f"进度: 100% - 同步完成")
        logger.info(f"同步完成: {success_count}/{total_tables} 个表同步成功")
        return success_count == total_tables
    
    def export_table_sql(self, connection, table_name: str, output_file, include_data: bool = True) -> bool:
        """导出表结构和数据为SQL"""
        try:
            # 导出表结构
            create_sql = self.get_table_structure(connection, table_name)
            if not create_sql:
                logger.error(f"无法获取表结构: {table_name}")
                return False
            
            # 写入表结构
            output_file.write(f"-- 表结构: {table_name}\n")
            output_file.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
            output_file.write(f"{create_sql};\n\n")
            
            # 导出表数据
            if include_data:
                columns = self.get_table_columns(connection, table_name)
                data = self.get_table_data(connection, table_name)
                
                if data:
                    output_file.write(f"-- 表数据: {table_name}\n")
                    
                    # 写入INSERT语句，每500条数据一组
                    batch_size = 500
                    columns_str = ', '.join([f'`{col}`' for col in columns])
                    
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i+batch_size]
                        values_list = []
                        
                        # 构建值列表
                        for row in batch:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                elif isinstance(val, (datetime)):
                                    values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                                elif isinstance(val, bytes):
                                    values.append(f"X'{val.hex()}'")
                                else:
                                    # 转义字符串中的单引号
                                    escaped = str(val).replace("'", "''")
                                    values.append(f"'{escaped}'")
                            values_list.append(f"({', '.join(values)})")
                        
                        # 写入INSERT语句
                        output_file.write(f"INSERT INTO `{table_name}` ({columns_str}) VALUES\n")
                        output_file.write(',\n'.join(values_list))
                        output_file.write(';\n\n')
                
            logger.info(f"表 {table_name} 导出完成")
            return True
        
        except Exception as e:
            logger.error(f"导出表 {table_name} 失败: {str(e)}")
            return False
    
    def export_database_sql(self, connection, output_path: str, exclude_tables: List[str] = None, include_tables: List[str] = None, include_data: bool = True) -> bool:
        """导出整个数据库为SQL文件"""
        if exclude_tables is None:
            exclude_tables = []
        
        # 获取数据库表列表
        tables = self.get_table_list(connection)
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
        
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # 打开输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头信息
            f.write(f"-- 机器人管理系统数据库导出\n")
            f.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 数据库: {connection.db.decode('utf-8')}\n")
            f.write(f"-- 主机: {connection.host}\n\n")
            
            # 写入数据库创建语句
            f.write(f"-- 创建数据库\n")
            f.write(f"CREATE DATABASE IF NOT EXISTS `{connection.db.decode('utf-8')}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\n")
            f.write(f"USE `{connection.db.decode('utf-8')}`;\n\n")
            
            # 禁用外键检查
            f.write("-- 禁用外键检查\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
            
            # 导出所有表
            success_count = 0
            total_tables = len(tables_to_export)
            
            for i, table in enumerate(tables_to_export):
                # 报告进度
                progress = int((i / total_tables) * 100)
                logger.info(f"进度: {progress}% - 正在导出表 {i+1}/{total_tables}: {table}")
                
                if self.export_table_sql(connection, table, f, include_data):
                    success_count += 1
                else:
                    logger.error(f"表 {table} 导出失败")
            
            # 启用外键检查
            f.write("-- 启用外键检查\n")
            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        
        # 最终进度更新
        logger.info(f"进度: 100% - 导出完成")
        logger.info(f"SQL导出完成: {output_path}")
        logger.info(f"共导出 {success_count}/{total_tables} 个表")
        return success_count == total_tables
    
    def execute_sql_file(self, connection, sql_file_path: str) -> Tuple[bool, List[str]]:
        """执行SQL文件"""
        try:
            # 读取SQL文件
            logger.info(f"读取SQL文件: {sql_file_path}")
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（以分号结尾）
            sql_statements = []
            current_statement = ""
            for line in sql_content.splitlines():
                # 跳过注释行
                stripped_line = line.strip()
                if stripped_line.startswith('--') or stripped_line.startswith('#'):
                    continue
                
                current_statement += line + " "
                if stripped_line.endswith(';'):
                    sql_statements.append(current_statement.strip())
                    current_statement = ""
            
            # 添加最后一个语句（如果没有以分号结尾）
            if current_statement.strip():
                sql_statements.append(current_statement.strip())
            
            logger.info(f"共解析 {len(sql_statements)} 条SQL语句")
            
            # 执行SQL语句
            errors = []
            success_count = 0
            total_statements = len(sql_statements)
            
            with connection.cursor() as cursor:
                for i, statement in enumerate(sql_statements):
                    if not statement.strip():
                        continue
                    
                    try:
                        cursor.execute(statement)
                        success_count += 1
                        
                        # 定期报告进度
                        if (i + 1) % 100 == 0 or (i + 1) == total_statements:
                            progress = int(((i + 1) / total_statements) * 100)
                            logger.info(f"进度: {progress}% - 已执行 {i + 1}/{total_statements} 条SQL语句")
                            connection.commit()  # 定期提交事务避免过大
                    except Exception as e:
                        errors.append(f"语句 {i + 1}: {str(e)}")
                        logger.error(f"SQL执行错误 (语句 {i + 1}): {str(e)}")
                
                # 提交事务
                connection.commit()
            
            if errors:
                logger.warning(f"SQL执行部分成功: {success_count}/{total_statements} 条语句执行成功，{len(errors)} 条语句执行失败")
                return False, errors
            else:
                logger.info(f"SQL执行成功: {success_count}/{total_statements} 条语句执行成功")
                return True, []
        
        except Exception as e:
            logger.error(f"SQL文件执行失败: {str(e)}")
            return False, [str(e)]
    
    def close_connections(self):
        """关闭数据库连接"""
        if self.source_conn:
            self.source_conn.close()
            logger.info("源数据库连接已关闭")
        
        if self.target_conn:
            self.target_conn.close()
            logger.info("目标数据库连接已关闭")

    def sync_remote_to_local(self) -> str:
        """从远程同步到本地"""
        try:
            # 设置目标数据库为本地数据库
            self.target_config = DatabaseConfig(
                host='localhost',
                port=3306,
                user=self.source_config.user,
                password=self.source_config.password,
                database=self.source_config.database
            )
            
            if not self.connect_databases():
                return "数据库连接失败"
            
            success = self.sync_all_tables()
            return "远程到本地同步完成" if success else "同步部分失败"
        
        except Exception as e:
            logger.error(f"远程到本地同步失败: {str(e)}")
            return f"同步失败: {str(e)}"
    
    def sync_local_to_remote(self) -> str:
        """从本地同步到远程"""
        try:
            # 交换源和目标配置
            self.source_config, self.target_config = self.target_config, self.source_config
            
            if not self.connect_databases():
                return "数据库连接失败"
            
            success = self.sync_all_tables()
            return "本地到远程同步完成" if success else "同步部分失败"
        
        except Exception as e:
            logger.error(f"本地到远程同步失败: {str(e)}")
            return f"同步失败: {str(e)}"
    
    def export_sql(self) -> str:
        """导出SQL文件"""
        try:
            conn = self.connect_single_database(self.source_config)
            if not conn:
                return "数据库连接失败"
            
            # 生成导出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"export_{self.source_config.database}_{timestamp}.sql"
            
            success = self.export_database_sql(conn, output_path)
            conn.close()
            
            return f"SQL导出成功: {output_path}" if success else "SQL导出部分失败"
        
        except Exception as e:
            logger.error(f"SQL导出失败: {str(e)}")
            return f"导出失败: {str(e)}"
    
    def execute_sql(self) -> str:
        """执行SQL文件"""
        try:
            conn = self.connect_single_database(self.source_config)
            if not conn:
                return "数据库连接失败"

            # 使用配置中的SQL文件路径
            sql_file = self.source_config.sql_file

            success, errors = self.execute_sql_file(conn, sql_file)
            conn.close()

            return f"SQL执行成功" if success else f"SQL执行部分失败: {len(errors)} 个错误"

        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            return f"执行失败: {str(e)}"

    def import_sql(self, sql_file_path: str) -> str:
        """导入SQL文件（与execute_sql功能相同，但提供更明确的语义）"""
        try:
            conn = self.connect_single_database(self.source_config)
            if not conn:
                return "数据库连接失败"

            logger.info(f"开始导入SQL文件: {sql_file_path}")

            # 验证文件存在
            if not os.path.exists(sql_file_path):
                return f"SQL文件不存在: {sql_file_path}"

            # 获取文件大小用于进度报告
            file_size = os.path.getsize(sql_file_path)
            logger.info(f"SQL文件大小: {file_size} 字节")

            success, errors = self.execute_sql_file(conn, sql_file_path)
            conn.close()

            if success:
                return f"SQL导入成功: {sql_file_path}"
            else:
                error_count = len(errors) if errors else 0
                return f"SQL导入部分完成: {error_count} 个错误"

        except Exception as e:
            logger.error(f"SQL导入失败: {str(e)}")
            return f"导入失败: {str(e)}"

    def export_sql_with_options(self, output_dir: str = None, include_data: bool = True,
                              exclude_tables: List[str] = None, include_tables: List[str] = None) -> str:
        """导出SQL文件（带更多选项）"""
        try:
            conn = self.connect_single_database(self.source_config)
            if not conn:
                return "数据库连接失败"

            # 生成导出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"export_{self.source_config.database}_{timestamp}.sql")
            else:
                output_path = f"export_{self.source_config.database}_{timestamp}.sql"

            logger.info(f"导出SQL到: {output_path}")
            logger.info(f"包含数据: {include_data}")

            if exclude_tables:
                logger.info(f"排除表: {exclude_tables}")
            if include_tables:
                logger.info(f"仅包含表: {include_tables}")

            success = self.export_database_sql(conn, output_path, exclude_tables, include_tables, include_data)
            conn.close()

            return f"SQL导出成功: {output_path}" if success else "SQL导出部分失败"

        except Exception as e:
            logger.error(f"SQL导出失败: {str(e)}")
            return f"导出失败: {str(e)}"

# 直接测试模块
if __name__ == "__main__":
    print("数据库同步模块 - 运行main.py来使用此模块") 