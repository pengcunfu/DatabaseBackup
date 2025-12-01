#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Tool - PySide6 Widgets Version Main Entry Point
使用传统 PySide6 Widgets 界面版本
"""

import sys
import os
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.db_config import create_default_config

# 配置日志
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_application():
    """设置应用程序"""
    # 现代PySide6版本默认支持高DPI，无需手动设置

    app = QApplication(sys.argv)
    app.setApplicationName("数据库备份同步工具")
    app.setOrganizationName("PyDatabaseBackup")

    # 设置应用图标
    icon_path = Path(__file__).parent / "resources" / "icon.png"
    if icon_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def main():
    """主函数 - PySide6 Widgets 界面"""
    try:
        # 确保配置文件存在
        if not os.path.exists('config.yaml'):
            create_default_config()
            logger.info("已创建默认配置文件")

        # 设置应用程序
        app = setup_application()

        # 导入并创建主窗口
        from app.main_window import MainWindow
        window = MainWindow()
        window.show()

        logger.info("PySide6 Widgets 界面启动成功")

        # 运行应用程序
        return app.exec()

    except ImportError as e:
        error_msg = f"导入模块失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"模块导入错误: {e}")
        return 1

    except Exception as e:
        error_msg = f"应用启动失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"GUI 启动失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
