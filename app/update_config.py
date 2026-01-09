"""
更新配置管理
"""
import json
from pathlib import Path
from typing import Dict, Any


class UpdateConfig:
    """更新配置类"""

    def __init__(self):
        self.config_file = Path.home() / ".databasebackup" / "update_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # 默认配置
        return {
            'auto_check': True,  # 是否自动检查更新
            'check_interval': 7,  # 检查间隔（天）
            'last_check': '',  # 上次检查时间
            'skipped_version': '',  # 跳过的版本
            'beta_updates': False,  # 是否接收测试版更新
        }

    def save_config(self):
        """保存配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
        self.save_config()

    def should_check_update(self) -> bool:
        """是否应该检查更新"""
        if not self.get('auto_check', True):
            return False

        from datetime import datetime, timedelta
        last_check = self.get('last_check', '')
        if not last_check:
            return True

        try:
            last_check_date = datetime.fromisoformat(last_check)
            interval_days = self.get('check_interval', 7)
            return datetime.now() - last_check_date > timedelta(days=interval_days)
        except Exception:
            return True

    def update_last_check(self):
        """更新上次检查时间"""
        from datetime import datetime
        self.set('last_check', datetime.now().isoformat())

    def is_version_skipped(self, version: str) -> bool:
        """检查版本是否被跳过"""
        return self.get('skipped_version', '') == version

    def skip_version(self, version: str):
        """跳过指定版本"""
        self.set('skipped_version', version)


# 全局配置实例
_update_config = None


def get_update_config() -> UpdateConfig:
    """获取更新配置实例（单例）"""
    global _update_config
    if _update_config is None:
        _update_config = UpdateConfig()
    return _update_config
