#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 配置管理器
用于管理数据库配置的 JSON 文件
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


# 支持的数据库类型
SUPPORTED_DB_TYPES = ["mysql", "sqlite", "postgresql"]

# 数据库类型显示名称
DB_TYPE_DISPLAY_NAMES = {
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "postgresql": "PostgreSQL"
}

# 数据库类型的默认端口
DB_TYPE_DEFAULT_PORTS = {
    "mysql": 3306,
    "postgresql": 5432,
    "sqlite": None  # SQLite 不需要端口
}


class ConfigManager:
    """JSON 配置管理器 - 支持多数据库类型"""

    @staticmethod
    def get_supported_db_types() -> List[str]:
        """获取支持的数据库类型列表"""
        return SUPPORTED_DB_TYPES.copy()

    @staticmethod
    def get_db_type_display_name(db_type: str) -> str:
        """获取数据库类型的显示名称"""
        return DB_TYPE_DISPLAY_NAMES.get(db_type.lower(), db_type)

    @staticmethod
    def get_default_port_for_db_type(db_type: str) -> Optional[int]:
        """获取数据库类型的默认端口"""
        return DB_TYPE_DEFAULT_PORTS.get(db_type.lower())
    
    def __init__(self, config_file: str = "resources/db_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config_data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                logger.info(f"配置已加载: {self.config_file}")
            else:
                # 创建默认配置
                self.config_data = self._get_default_config()
                self._save_config()
                logger.info(f"创建默认配置: {self.config_file}")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.config_data = self._get_default_config()
    
    def _save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            logger.info(f"配置已保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "local": {
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "username": "root",
                "password": "",
                "database": "local_db"
            },
            "remote": {
                "db_type": "mysql",
                "host": "192.168.1.100",
                "port": 3306,
                "username": "root",
                "password": "",
                "database": "remote_db"
            },
            "sync_options": {
                "exclude_tables": [],
                "include_tables": [],
                "drop_target_tables": True,
                "convert_data_types": True
            }
        }
    
    def get_local_config(self) -> Dict[str, Any]:
        """获取本地数据库配置"""
        return self.config_data.get("local", {})
    
    def get_remote_config(self) -> Dict[str, Any]:
        """获取远程数据库配置"""
        return self.config_data.get("remote", {})
    
    def get_sync_options(self) -> Dict[str, Any]:
        """获取同步选项"""
        return self.config_data.get("sync_options", {})
    
    def set_local_config(self, config: Dict[str, Any]) -> bool:
        """
        设置本地数据库配置
        
        Args:
            config: 配置字典
        
        Returns:
            是否保存成功
        """
        self.config_data["local"] = config
        return self._save_config()
    
    def set_remote_config(self, config: Dict[str, Any]) -> bool:
        """
        设置远程数据库配置
        
        Args:
            config: 配置字典
        
        Returns:
            是否保存成功
        """
        self.config_data["remote"] = config
        return self._save_config()
    
    def set_both_configs(self, local_config: Dict[str, Any], remote_config: Dict[str, Any]) -> bool:
        """
        同时设置本地和远程配置
        
        Args:
            local_config: 本地配置字典
            remote_config: 远程配置字典
        
        Returns:
            是否保存成功
        """
        self.config_data["local"] = local_config
        self.config_data["remote"] = remote_config
        return self._save_config()
    
    def set_sync_options(self, options: Dict[str, Any]) -> bool:
        """
        设置同步选项
        
        Args:
            options: 同步选项字典
        
        Returns:
            是否保存成功
        """
        self.config_data["sync_options"] = options
        return self._save_config()
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_data.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证配置是否有效

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误信息)
        """
        # 获取数据库类型
        db_type = config.get("db_type", "mysql")

        # 根据数据库类型验证不同的必填字段
        if db_type == "sqlite":
            # SQLite 只需要数据库文件路径
            if "database" not in config or not config["database"]:
                return False, "缺少必填字段: database (数据库文件路径)"
        else:
            # MySQL 和 PostgreSQL 需要 host, port, username, database
            required_fields = ["host", "port", "username", "database"]
            for field in required_fields:
                if field not in config or not config[field]:
                    return False, f"缺少必填字段: {field}"

            # 验证端口号
            try:
                port = int(config["port"])
                if port < 1 or port > 65535:
                    return False, "端口号必须在 1-65535 之间"
            except (ValueError, TypeError):
                return False, "端口号必须是有效的整数"

        return True, ""
    
    def export_config(self, export_path: str) -> bool:
        """
        导出配置到指定路径
        
        Args:
            export_path: 导出文件路径
        
        Returns:
            是否导出成功
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            logger.info(f"配置已导出: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        从指定路径导入配置
        
        Args:
            import_path: 导入文件路径
        
        Returns:
            是否导入成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # 验证导入的配置
            if "local" in imported_data and "remote" in imported_data:
                self.config_data = imported_data
                self._save_config()
                logger.info(f"配置已导入: {import_path}")
                return True
            else:
                logger.error("导入的配置格式不正确")
                return False
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
