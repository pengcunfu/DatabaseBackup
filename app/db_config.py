#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具 - 配置管理模块
用于加载、保存和管理YAML配置文件的功能
"""

import base64
import os
import sys
import logging
from typing import Dict, Any, Optional, List

try:
    import yaml
except ImportError:
    print("错误: PyYAML库未安装")
    print("安装命令: pip install pyyaml")
    sys.exit(1)

# 获取日志记录器（不重复配置）
logger = logging.getLogger(__name__)

# 默认配置文件路径
CONFIG_FILE = 'config.yaml'

def encrypt_password(password: str) -> str:
    """简单密码加密"""
    return base64.b64encode(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    return base64.b64decode(encrypted_password.encode()).decode()

class DatabaseConfig:
    def __init__(
        self, 
        name: str = 'default',
        host: str = 'localhost', 
        port: int = 3306,
        username: str = 'root', 
        password: str = '', 
        database: str = '',
        sql_file: str = ''
    ):
        # 数据库配置
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self._password = encrypt_password(password)
        self.database = database
        
        # SQL文件路径
        self.sql_file = sql_file

    @property
    def password(self) -> str:
        """获取解密后的密码"""
        return decrypt_password(self._password)

    @password.setter
    def password(self, value: str):
        """设置并加密密码"""
        self._password = encrypt_password(value)

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'database': self.database
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"DatabaseConfig(name={self.name}, host={self.host}:{self.port}/{self.database})"

    def save_config(self, config_path: str = CONFIG_FILE) -> None:
        """保存配置到YAML文件"""
        try:
            # 读取现有配置
            config = self.load_all_configs()
            
            # 更新或添加当前配置
            config[self.name] = {
                'host': self.host,
                'port': self.port,
                'username': self.username,
                'password': self._password,
                'database': self.database
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump({'databases': config}, f, allow_unicode=True)
            
            logger.info(f"配置 {self.name} 已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    @classmethod
    def load_config(cls, name: str = 'default', config_path: str = CONFIG_FILE) -> 'DatabaseConfig':
        """从YAML文件加载特定名称的配置"""
        try:
            if not os.path.exists(config_path):
                logger.warning(f"配置文件 {config_path} 不存在")
                return cls(name=name)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            databases = config_data.get('databases', {})
            db_config = databases.get(name, {})
            
            return cls(
                name=name,
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                username=db_config.get('username', 'root'),
                password=decrypt_password(db_config.get('password', '')),
                database=db_config.get('database', '')
            )
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return cls(name=name)

    @classmethod
    def load_all_configs(cls, config_path: str = CONFIG_FILE) -> Dict[str, Dict[str, Any]]:
        """加载所有数据库配置"""
        try:
            if not os.path.exists(config_path):
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return config_data.get('databases', {})
        except Exception as e:
            logger.error(f"加载所有配置失败: {e}")
            return {}

def create_default_config(config_file: str = CONFIG_FILE) -> bool:
    """创建默认配置文件"""
    default_config = {
        'databases': {
            'local': {
                'host': 'localhost',
                'port': 3306,
                'username': 'root',
                'password': encrypt_password('local_password'),
                'database': 'robot_management_local'
            },
            'remote': {
                'host': '192.168.1.100',
                'port': 3306,
                'username': 'root',
                'password': encrypt_password('remote_password'),
                'database': 'robot_management'
            }
        },
        'sync_options': {
            'exclude_tables': ['user_sessions', 'login_attempts'],
            'include_tables': [],
            'drop_target_tables': True
        }
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(default_config, f, allow_unicode=True)
        logger.info(f"默认配置文件已创建: {config_file}")
        return True
    except Exception as e:
        logger.error(f"创建默认配置文件失败: {e}")
        return False

def get_database_configs(config: Dict) -> tuple:
    """从配置字典中提取源和目标数据库配置"""
    source_config = DatabaseConfig.from_dict(config.get('source', {}))
    target_config = DatabaseConfig.from_dict(config.get('target', {}))
    
    return source_config, target_config

def get_sync_options(config: Dict) -> Dict:
    """从配置字典中提取同步选项"""
    return config.get('sync_options', {})

# 直接测试模块
if __name__ == "__main__":
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    
    # 演示多配置管理
    local_config = DatabaseConfig.load_config('local')
    remote_config = DatabaseConfig.load_config('remote')
    
    print("本地数据库配置:", local_config)
    print("远程数据库配置:", remote_config) 