#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具 - 主界面模块
使用 PySide6 Widgets 的传统界面
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QComboBox, QPushButton, QTextEdit, QLabel, QProgressBar,
    QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QIcon, QAction, QFont

from .db_config import DatabaseConfig, create_default_config
from .db_sync import DatabaseSynchronizer
from .config_manager import get_config_manager
from .config_dialog import ConfigDialog

logger = logging.getLogger(__name__)


class SyncWorker(QThread):
    """后台同步工作线程"""
    log_updated = Signal(str)
    sync_finished = Signal(bool, str)
    progress_updated = Signal(int)

    def __init__(self, sync_type, config, sql_file=""):
        super().__init__()
        self.sync_type = sync_type
        self.config = config
        self.sql_file = sql_file

    def run(self):
        """执行同步任务"""
        try:
            sync = DatabaseSynchronizer(self.config)

            self.log_updated.emit(f"[INFO] 开始执行: {self.sync_type}")

            if self.sync_type == '远程到本地':
                result = sync.sync_remote_to_local()
            elif self.sync_type == '本地到远程':
                result = sync.sync_local_to_remote()
            elif self.sync_type == '导出SQL':
                result = sync.export_sql()
            elif self.sync_type == '执行SQL':
                if not self.sql_file or not os.path.exists(self.sql_file):
                    self.sync_finished.emit(False, "SQL 文件不存在")
                    return
                self.config.sql_file = self.sql_file
                result = sync.execute_sql()
            else:
                result = "未知的同步类型"
                self.sync_finished.emit(False, result)
                return

            self.log_updated.emit(f"[INFO] {result}")
            self.sync_finished.emit(True, result)

        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_updated.emit(f"[ERROR] {error_msg}")
            self.sync_finished.emit(False, error_msg)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.config_manager = get_config_manager()
        self.sql_file_path = ""

        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()

        # 加载配置
        QTimer.singleShot(100, self.load_config)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("数据库备份同步工具")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # 设置应用图标
        icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 同步模式和按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        control_layout.addWidget(QLabel("同步模式:"))

        self.sync_type_combo = QComboBox()
        self.sync_type_combo.addItems(["远程到本地", "本地到远程", "导出SQL", "执行SQL"])
        self.sync_type_combo.currentTextChanged.connect(self.on_sync_type_changed)
        control_layout.addWidget(self.sync_type_combo)

        self.start_button = QPushButton("开始同步")
        self.start_button.clicked.connect(self.start_sync)
        self.start_button.setMinimumWidth(100)
        control_layout.addWidget(self.start_button)

        main_layout.addLayout(control_layout)

        # SQL 文件选择区域
        self.sql_frame = QFrame()
        sql_layout = QHBoxLayout(self.sql_frame)
        sql_layout.setSpacing(8)
        sql_layout.setContentsMargins(0, 0, 0, 0)

        sql_layout.addWidget(QLabel("SQL 文件:"))

        self.sql_file_input = QTextEdit()
        self.sql_file_input.setMaximumHeight(30)
        self.sql_file_input.setReadOnly(True)
        self.sql_file_input.setPlaceholderText("选择 SQL 文件")
        sql_layout.addWidget(self.sql_file_input)

        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.select_sql_file)
        self.browse_button.setMinimumWidth(80)
        sql_layout.addWidget(self.browse_button)

        self.sql_frame.setVisible(False)  # 默认隐藏
        main_layout.addWidget(self.sql_frame)

        # 日志面板
        log_group = QGroupBox("同步日志")
        log_layout = QVBoxLayout(log_group)

        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        log_control_layout.addWidget(QLabel("日志输出:"))
        log_control_layout.addStretch()

        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.clear_log_button.setMinimumWidth(80)
        log_control_layout.addWidget(self.clear_log_button)

        log_layout.addLayout(log_control_layout)

        # 日志文本区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_output)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        log_layout.addWidget(self.progress_bar)

        main_layout.addWidget(log_group)

    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        config_action = QAction("配置数据库", self)
        config_action.triggered.connect(self.show_config_dialog)
        file_menu.addAction(config_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        clear_log_action = QAction("清空日志", self)
        clear_log_action.triggered.connect(self.clear_log)
        tools_menu.addAction(clear_log_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)

        config_action = QAction("配置", self)
        config_action.triggered.connect(self.show_config_dialog)
        toolbar.addAction(config_action)

        toolbar.addSeparator()

        self.start_action = QAction("开始同步", self)
        self.start_action.triggered.connect(self.start_sync)
        toolbar.addAction(self.start_action)

    def init_statusbar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.addPermanentWidget(QLabel("v1.0.0"))
        self.status_bar.addPermanentWidget(QLabel("© 2025 Database Backup Tool"))

    def on_sync_type_changed(self, sync_type):
        """同步类型改变时的处理"""
        is_sql_mode = sync_type == "执行SQL"
        self.sql_frame.setVisible(is_sql_mode)

        if not is_sql_mode:
            self.sql_file_path = ""
            self.sql_file_input.clear()

    def select_sql_file(self):
        """选择SQL文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SQL 文件",
            "",
            "SQL Files (*.sql);;All Files (*)"
        )

        if file_path:
            self.sql_file_path = file_path
            self.sql_file_input.setText(file_path)
            self.log_output.append(f"[INFO] 已选择 SQL 文件: {file_path}")

    def start_sync(self):
        """开始同步"""
        sync_type = self.sync_type_combo.currentText()

        if sync_type == "执行SQL" and not self.sql_file_path:
            QMessageBox.warning(self, "警告", "请选择 SQL 文件")
            return

        try:
            # 从配置管理器读取配置
            local_config = self.config_manager.get_local_config()
            remote_config = self.config_manager.get_remote_config()

            # 根据同步类型选择配置
            if sync_type == "远程到本地":
                source_config = remote_config
                target_config = local_config
                self.log_output.append("[INFO] 模式: 远程到本地")
                self.log_output.append(f"  源: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
                self.log_output.append(f"  目标: {target_config.get('host')}:{target_config.get('port')}/{target_config.get('database')}")
            elif sync_type == "本地到远程":
                source_config = local_config
                target_config = remote_config
                self.log_output.append("[INFO] 模式: 本地到远程")
                self.log_output.append(f"  源: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
                self.log_output.append(f"  目标: {target_config.get('host')}:{target_config.get('port')}/{target_config.get('database')}")
            elif sync_type == "导出SQL":
                source_config = local_config
                self.log_output.append("[INFO] 模式: 导出SQL")
                self.log_output.append(f"  数据库: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
            elif sync_type == "执行SQL":
                target_config = local_config
                self.log_output.append("[INFO] 模式: 执行SQL")
                self.log_output.append(f"  目标: {target_config.get('host')}:{target_config.get('port')}/{target_config.get('database')}")
                self.log_output.append(f"  文件: {self.sql_file_path}")
            else:
                self.log_output.append(f"[ERROR] 未知的同步类型: {sync_type}")
                return

            self.log_output.append("")

            # 验证配置
            if sync_type in ["远程到本地", "本地到远程"]:
                valid, msg = self.config_manager.validate_config(source_config)
                if not valid:
                    self.log_output.append(f"[ERROR] 源数据库配置无效: {msg}")
                    QMessageBox.critical(self, "错误", f"源数据库配置无效: {msg}")
                    return

                valid, msg = self.config_manager.validate_config(target_config)
                if not valid:
                    self.log_output.append(f"[ERROR] 目标数据库配置无效: {msg}")
                    QMessageBox.critical(self, "错误", f"目标数据库配置无效: {msg}")
                    return

                # 创建数据库配置对象
                config = DatabaseConfig(
                    host=source_config.get('host'),
                    port=source_config.get('port'),
                    username=source_config.get('username'),
                    password=source_config.get('password'),
                    database=source_config.get('database')
                )
            else:
                # 导出SQL或执行SQL只需要一个配置
                use_config = source_config if sync_type == "导出SQL" else target_config
                valid, msg = self.config_manager.validate_config(use_config)
                if not valid:
                    self.log_output.append(f"[ERROR] 数据库配置无效: {msg}")
                    QMessageBox.critical(self, "错误", f"数据库配置无效: {msg}")
                    return

                config = DatabaseConfig(
                    host=use_config.get('host'),
                    port=use_config.get('port'),
                    username=use_config.get('username'),
                    password=use_config.get('password'),
                    database=use_config.get('database')
                )

            # 开始同步
            self.set_syncing_state(True)

            # 创建并启动工作线程
            self.worker = SyncWorker(sync_type, config, self.sql_file_path)
            self.worker.log_updated.connect(self.on_log_updated)
            self.worker.sync_finished.connect(self.on_sync_finished)
            self.worker.start()

        except Exception as e:
            error_msg = f"启动同步失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_output.append(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)

    def set_syncing_state(self, syncing):
        """设置同步状态"""
        self.start_button.setEnabled(not syncing)
        self.start_action.setEnabled(not syncing)
        self.sync_type_combo.setEnabled(not syncing)
        self.browse_button.setEnabled(not syncing)

        if syncing:
            self.progress_bar.setVisible(True)
            self.status_label.setText("正在同步...")
        else:
            self.progress_bar.setVisible(False)

    def on_log_updated(self, message):
        """日志更新处理"""
        self.log_output.append(message)
        # 自动滚动到底部
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def on_sync_finished(self, success, message):
        """同步完成处理"""
        self.set_syncing_state(False)

        if success:
            self.status_label.setText("同步完成")
            self.log_output.append(f"\n✓ {message}\n")
        else:
            self.status_label.setText("同步失败")
            self.log_output.append(f"\n✗ {message}\n")

    def clear_log(self):
        """清空日志"""
        self.log_output.clear()

    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self)
        if dialog.exec() == ConfigDialog.Accepted:
            self.log_output.append("[SUCCESS] ✓ 配置已保存")

    def load_config(self):
        """加载配置"""
        try:
            # 验证配置文件是否存在
            if not os.path.exists('config.yaml'):
                create_default_config()
                self.log_output.append("[INFO] 已创建默认配置文件")

            local_config = self.config_manager.get_local_config()
            remote_config = self.config_manager.get_remote_config()

            if local_config and remote_config:
                self.log_output.append("[INFO] 配置加载成功")
            else:
                self.log_output.append("[WARNING] 配置文件为空，请配置数据库连接")

        except Exception as e:
            error_msg = f"加载配置失败: {str(e)}"
            logger.error(error_msg)
            self.log_output.append(f"[ERROR] {error_msg}")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于",
            "数据库备份同步工具\n"
            "版本: 1.0.0\n"
            "基于 PySide6 开发的数据库管理工具\n\n"
            "© 2025 Database Backup Tool"
        )

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "同步任务正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

            # 终止工作线程
            self.worker.terminate()
            self.worker.wait()

        event.accept()


def main():
    """主函数"""
    try:
        # 确保配置文件存在
        if not os.path.exists('config.yaml'):
            create_default_config()

        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("数据库备份同步工具")
        app.setOrganizationName("PyDatabaseBackup")

        # 创建主窗口
        window = MainWindow()
        window.show()

        # 运行应用
        return app.exec()

    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        print(f"GUI 启动失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())