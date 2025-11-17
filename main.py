#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Tool - QML Version Main Entry Point
使用 Qt Quick (QML) 的现代化界面版本
"""

import sys
import os
import argparse
import logging
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from app.db_config import DatabaseConfig, create_default_config
from app.qml_backend import QMLBackend

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


def setup_qml_engine():
    """设置 QML 引擎"""
    # 设置 Qt Quick Controls 样式为 Windows 11 风格
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Universal"
    
    # 创建应用
    app = QGuiApplication(sys.argv)
    app.setApplicationName("数据库备份同步工具")
    app.setOrganizationName("PyDatabaseBackup")
    
    # 设置应用图标
    icon_path = Path(__file__).parent / "resource" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 创建 QML 引擎
    engine = QQmlApplicationEngine()
    
    # 创建后端对象
    backend = QMLBackend()
    
    # 注册后端对象到 QML 上下文
    engine.rootContext().setContextProperty("backend", backend)
    
    # 加载 QML 文件
    qml_file = Path(__file__).parent / "qml" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    # 检查是否加载成功
    if not engine.rootObjects():
        logger.error("QML 文件加载失败")
        return None, None
    
    logger.info("QML 界面加载成功")
    return app, engine


def main_qml():
    """QML 图形界面模式"""
    try:
        # 确保配置文件存在
        if not os.path.exists('config.yaml'):
            create_default_config()
        
        # 设置并启动 QML 应用
        app, engine = setup_qml_engine()
        
        if app is None:
            logger.error("应用初始化失败")
            return 1
        
        # 运行应用
        return app.exec()
        
    except Exception as e:
        logger.error(f"QML 模式异常: {e}", exc_info=True)
        print(f"GUI 启动失败: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库同步工具 (QML 版本)')
    parser.add_argument(
        '--style',
        choices=['Universal', 'Material', 'Fusion', 'Windows'],
        default='Universal',
        help='Qt Quick Controls 样式'
    )
    
    args = parser.parse_args()
    
    # 设置样式
    if args.style:
        os.environ["QT_QUICK_CONTROLS_STYLE"] = args.style
        logger.info(f"使用样式: {args.style}")
    
    return main_qml()


if __name__ == '__main__':
    sys.exit(main())
