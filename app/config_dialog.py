#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具 - 配置对话框模块
使用 PySide6 Widgets 的配置对话框
"""

import logging
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QFormLayout, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .config_manager import get_config_manager, ConfigManager

logger = logging.getLogger(__name__)


class DatabaseConfigWidget(QWidget):
    """数据库配置组件 - 支持多数据库类型"""

    def __init__(self, title="数据库配置", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # 配置表单
        form_group = QGroupBox()
        form_layout = QFormLayout(form_group)

        # 数据库类型
        self.db_type_combo = QComboBox()
        for db_type in ConfigManager.get_supported_db_types():
            self.db_type_combo.addItem(ConfigManager.get_db_type_display_name(db_type), db_type)
        self.db_type_combo.currentIndexChanged.connect(self.on_db_type_changed)
        form_layout.addRow("数据库类型:", self.db_type_combo)

        # 主机地址
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("localhost")
        form_layout.addRow("主机地址:", self.host_edit)

        # 端口
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("3306")
        form_layout.addRow("端口:", self.port_edit)

        # 用户名
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("root")
        form_layout.addRow("用户名:", self.username_edit)

        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form_layout.addRow("密码:", self.password_edit)

        # 数据库名/文件路径
        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("请输入数据库名")
        self.database_label = QLabel("数据库名:")
        form_layout.addRow(self.database_label, self.database_edit)

        layout.addWidget(form_group)
        layout.addStretch()

        # 初始化为 MySQL
        self.on_db_type_changed(0)

    def on_db_type_changed(self, index):
        """数据库类型改变时的处理"""
        db_type = self.db_type_combo.currentData()

        if db_type == "sqlite":
            # SQLite 只需要数据库文件路径
            self.host_edit.setEnabled(False)
            self.host_edit.clear()
            self.port_edit.setEnabled(False)
            self.port_edit.clear()
            self.username_edit.setEnabled(False)
            self.username_edit.clear()
            self.password_edit.setEnabled(False)
            self.password_edit.clear()
            self.database_label.setText("数据库文件:")
            self.database_edit.setPlaceholderText("例如: data/my_database.db")
        else:
            # MySQL 和 PostgreSQL 需要完整的连接信息
            self.host_edit.setEnabled(True)
            self.port_edit.setEnabled(True)
            self.username_edit.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.database_label.setText("数据库名:")

            # 设置默认值
            if not self.host_edit.text():
                self.host_edit.setPlaceholderText("localhost")

            if not self.port_edit.text():
                default_port = ConfigManager.get_default_port_for_db_type(db_type)
                if default_port:
                    self.port_edit.setPlaceholderText(str(default_port))

            if not self.username_edit.text():
                if db_type == "mysql":
                    self.username_edit.setPlaceholderText("root")
                elif db_type == "postgresql":
                    self.username_edit.setPlaceholderText("postgres")

            self.database_edit.setPlaceholderText("请输入数据库名")

    def load_config(self, config: Dict):
        """加载配置"""
        if not config:
            return

        # 加载数据库类型
        db_type = config.get('db_type', 'mysql')
        for i in range(self.db_type_combo.count()):
            if self.db_type_combo.itemData(i) == db_type:
                self.db_type_combo.setCurrentIndex(i)
                break

        # 加载其他配置
        self.host_edit.setText(config.get('host', ''))
        self.port_edit.setText(str(config.get('port', '')) if config.get('port') else '')
        self.username_edit.setText(config.get('username', ''))
        self.password_edit.setText(config.get('password', ''))
        self.database_edit.setText(config.get('database', ''))

    def get_config(self) -> Dict:
        """获取配置"""
        db_type = self.db_type_combo.currentData()

        config = {
            'db_type': db_type,
            'database': self.database_edit.text() or ''
        }

        # SQLite 不需要 host, port, username
        if db_type != 'sqlite':
            try:
                port = int(self.port_edit.text()) if self.port_edit.text() else 3306
            except ValueError:
                port = ConfigManager.get_default_port_for_db_type(db_type) or 3306

            config.update({
                'host': self.host_edit.text() or 'localhost',
                'port': port,
                'username': self.username_edit.text() or 'root',
                'password': self.password_edit.text() or ''
            })

        return config

    def clear_config(self):
        """清空配置"""
        self.db_type_combo.setCurrentIndex(0)
        self.host_edit.clear()
        self.port_edit.clear()
        self.username_edit.clear()
        self.password_edit.clear()
        self.database_edit.clear()


class ConfigDialog(QDialog):
    """配置对话框"""

    test_connection_result = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("数据库配置")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # 标签页
        self.tab_widget = QTabWidget()

        # 本地数据库配置
        self.local_config_widget = DatabaseConfigWidget("本地数据库配置")
        self.tab_widget.addTab(self.local_config_widget, "本地数据库")

        # 远程数据库配置
        self.remote_config_widget = DatabaseConfigWidget("远程数据库配置")
        self.tab_widget.addTab(self.remote_config_widget, "远程数据库")

        layout.addWidget(self.tab_widget)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        # 对话框按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

        # 连接测试结果信号
        self.test_connection_result.connect(self.on_test_connection_result)

    def load_config(self):
        """加载配置"""
        try:
            local_config = self.config_manager.get_local_config()
            remote_config = self.config_manager.get_remote_config()

            self.local_config_widget.load_config(local_config)
            self.remote_config_widget.load_config(remote_config)

            logger.info("配置已加载到界面")

        except Exception as e:
            error_msg = f"加载配置失败: {str(e)}"
            logger.error(error_msg)

    def save_config(self) -> bool:
        """保存配置"""
        try:
            local_config = self.local_config_widget.get_config()
            remote_config = self.remote_config_widget.get_config()

            # 验证本地配置
            valid, msg = self.config_manager.validate_config(local_config)
            if not valid:
                QMessageBox.critical(self, "错误", f"本地配置无效: {msg}")
                return False

            # 验证远程配置
            valid, msg = self.config_manager.validate_config(remote_config)
            if not valid:
                QMessageBox.critical(self, "错误", f"远程配置无效: {msg}")
                return False

            # 保存配置
            success = self.config_manager.set_both_configs(local_config, remote_config)

            if success:
                logger.info("配置保存成功")
                return True
            else:
                QMessageBox.critical(self, "错误", "配置保存失败")
                return False

        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            return False

    def test_connection(self):
        """测试数据库连接"""
        try:
            current_index = self.tab_widget.currentIndex()

            if current_index == 0:
                config = self.local_config_widget.get_config()
                config_type = "本地"
            else:
                config = self.remote_config_widget.get_config()
                config_type = "远程"

            # 验证配置完整性
            db_type = config.get('db_type', 'mysql')

            if db_type == 'sqlite':
                if not config.get('database'):
                    QMessageBox.warning(self, "警告", f"{config_type}数据库配置信息不完整")
                    return
            else:
                if not config.get('host') or not config.get('username') or not config.get('database'):
                    QMessageBox.warning(self, "警告", f"{config_type}数据库配置信息不完整")
                    return

            self.test_button.setEnabled(False)
            self.test_button.setText("测试中...")

            # 使用适配器测试连接
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

            from app.db_adapters import get_adapter

            adapter = get_adapter(db_type, config)
            success, message = adapter.test_connection()

            if success:
                self.test_connection_result.emit(True, f"{config_type}数据库连接成功!")
            else:
                self.test_connection_result.emit(False, f"{config_type}数据库连接失败: {message}")

        except Exception as e:
            error_msg = f"{config_type}数据库连接失败: {str(e)}"
            self.test_connection_result.emit(False, error_msg)

    def on_test_connection_result(self, success, message):
        """测试连接结果处理"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试连接")

        if success:
            QMessageBox.information(self, "连接成功", message)
        else:
            QMessageBox.critical(self, "连接失败", message)

    def accept(self):
        """确认按钮处理"""
        if self.save_config():
            super().accept()


# 直接测试模块
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = ConfigDialog()
    if dialog.exec() == QDialog.Accepted:
        print("配置已保存")

    sys.exit()