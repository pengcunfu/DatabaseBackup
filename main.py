#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Tool - Main Entry Point
Provides command-line interface and GUI launcher for database operations
"""

import sys
import os
import argparse
import logging
from typing import Optional

from app.db_config import DatabaseConfig, create_default_config
from app.db_sync import DatabaseSynchronizer
from app.db_gui import DatabaseSyncApp

# 配置日志
os.makedirs('logs', exist_ok=True)  # 确保logs目录存在
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_config(config: DatabaseConfig) -> bool:
    """验证数据库配置是否有效"""
    if not config.host or not config.username or not config.database:
        logger.error("数据库配置不完整")
        return False
    return True

def sync_databases(source_name: str, target_name: str) -> Optional[str]:
    """同步两个数据库配置"""
    try:
        source_config = DatabaseConfig.load_config(source_name)
        target_config = DatabaseConfig.load_config(target_name)

        if not validate_config(source_config) or not validate_config(target_config):
            return "数据库配置验证失败"

        sync = DatabaseSynchronizer(source_config, target_config)
        
        if not sync.connect_databases():
            return "数据库连接失败"

        # 获取同步选项
        all_configs = DatabaseConfig.load_all_configs()
        sync_options = all_configs.get('sync_options', {})
        
        exclude_tables = sync_options.get('exclude_tables', [])
        include_tables = sync_options.get('include_tables', [])
        drop_target_tables = sync_options.get('drop_target_tables', True)

        # 执行同步
        success = sync.sync_all_tables(
            exclude_tables=exclude_tables, 
            include_tables=include_tables
        )

        sync.close_connections()
        
        return "数据库同步成功" if success else "数据库同步失败"

    except Exception as e:
        logger.error(f"数据库同步异常: {e}")
        return f"同步异常: {e}"

def cli_mode(args):
    """命令行模式"""
    try:
        if not os.path.exists('config.yaml'):
            create_default_config()

        if args.mode == 'sync':
            result = sync_databases(args.source, args.target)
        elif args.mode == 'export':
            config = DatabaseConfig.load_config(args.database)
            sync = DatabaseSynchronizer(config)
            result = sync.export_database_sql(
                sync.connect_single_database(config), 
                args.output, 
                include_data=args.include_data
            )
        elif args.mode == 'execute':
            config = DatabaseConfig.load_config(args.database)
            sync = DatabaseSynchronizer(config)
            result = sync.execute_sql_file(
                sync.connect_single_database(config), 
                args.sql_file
            )
        else:
            result = "无效的操作模式"

        print(result)
    except Exception as e:
        logger.error(f"CLI模式异常: {e}")
        print(f"错误: {e}")

def gui_mode():
    """图形界面模式"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = DatabaseSyncApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"GUI模式异常: {e}")
        print(f"GUI启动失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='数据库同步工具')
    parser.add_argument(
        '--mode', 
        choices=['gui', 'sync', 'export', 'execute'], 
        default='gui',
        help='运行模式'
    )
    
    # 同步模式参数
    parser.add_argument('--source', default='local', help='源数据库配置名')
    parser.add_argument('--target', default='remote', help='目标数据库配置名')
    
    # 导出模式参数
    parser.add_argument('--database', default='local', help='数据库配置名')
    parser.add_argument('--output', default='database_export.sql', help='导出SQL文件路径')
    parser.add_argument('--include-data', action='store_true', help='导出是否包含数据')
    
    # 执行SQL参数
    parser.add_argument('--sql-file', help='要执行的SQL文件路径')

    args = parser.parse_args()

    if args.mode == 'gui':
        gui_mode()
    else:
        cli_mode(args)

if __name__ == '__main__':
    main() 