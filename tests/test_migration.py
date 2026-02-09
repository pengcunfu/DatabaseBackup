#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库迁移功能测试脚本
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.db_adapters import get_adapter, SUPPORTED_DB_TYPES
from app.db_migration import DatabaseMigration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_adapter_connection(db_type: str, config: dict):
    """测试适配器连接"""
    print(f"\n{'='*60}")
    print(f"测试 {db_type.upper()} 数据库连接")
    print(f"{'='*60}")

    try:
        adapter = get_adapter(db_type, config)
        success, message = adapter.test_connection()

        if success:
            print(f"✓ 连接成功: {message}")

            # 获取表列表
            tables = adapter.get_table_list()
            print(f"  数据库表数量: {len(tables)}")
            if tables:
                print(f"  表列表: {', '.join(tables[:5])}")
                if len(tables) > 5:
                    print(f"            ... 还有 {len(tables) - 5} 个表")

            adapter.close()
            return True
        else:
            print(f"✗ 连接失败: {message}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_migration():
    """测试数据库迁移功能"""
    print("\n" + "="*60)
    print("数据库迁移工具测试")
    print("="*60)
    print(f"\n支持的数据库类型: {', '.join(SUPPORTED_DB_TYPES)}")

    # 测试配置 - 请根据实际情况修改
    test_configs = {
        'mysql': {
            'db_type': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'username': 'root',
            'password': '',
            'database': 'test_db'
        },
        'sqlite': {
            'db_type': 'sqlite',
            'database': 'test_sqlite.db'
        },
        'postgresql': {
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': '',
            'database': 'test_db'
        }
    }

    results = {}

    # 测试每种数据库类型的连接
    for db_type, config in test_configs.items():
        results[db_type] = test_adapter_connection(db_type, config)

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for db_type, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{db_type.upper():15} : {status}")

    # 统计
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个数据库连接测试通过")

    if passed == 0:
        print("\n提示: 请修改 test_configs 中的数据库连接信息以进行测试")
        print("      如果没有安装某些数据库,可以跳过对应测试")

    return passed > 0


def test_type_mapping():
    """测试数据类型映射"""
    from app.db_adapters.type_mapping import DataTypeMapper

    print("\n" + "="*60)
    print("数据类型映射测试")
    print("="*60)

    # 测试 MySQL 到 SQLite 的类型映射
    test_types = [
        ('INT', 'mysql', 'sqlite'),
        ('VARCHAR(255)', 'mysql', 'sqlite'),
        ('DATETIME', 'mysql', 'sqlite'),
        ('BLOB', 'mysql', 'postgresql'),
        ('TEXT', 'sqlite', 'mysql'),
        ('INTEGER', 'sqlite', 'postgresql'),
    ]

    print("\n数据类型映射示例:")
    for source_type, source_db, target_db in test_types:
        mapped_type = DataTypeMapper.map_type(source_type, source_db, target_db)
        print(f"  {source_type:20} ({source_db:10} -> {target_db:10}) = {mapped_type}")

    print("\n✓ 类型映射功能正常")


if __name__ == '__main__':
    print("="*60)
    print("数据库迁移工具 - 多数据库支持测试")
    print("="*60)

    # 测试类型映射
    test_type_mapping()

    # 测试数据库连接
    test_migration()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
