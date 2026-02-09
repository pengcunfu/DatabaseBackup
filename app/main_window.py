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
    QMessageBox, QGroupBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QDialog, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QIcon, QAction, QFont

from .db_config import DatabaseConfig, create_default_config
from .db_sync import DatabaseSynchronizer
from .db_migration import DatabaseMigration
from .config_manager import get_config_manager
from .config_dialog import ConfigDialog
from .task_scheduler import TaskScheduler
from .task_dialog import TaskDialog
from .scheduler_config import ScheduledTask
from .update_manager import UpdateManager, get_current_version
from .update_config import get_update_config

logger = logging.getLogger(__name__)


class SyncWorker(QThread):
    """后台同步/迁移工作线程"""
    log_updated = Signal(str)
    sync_finished = Signal(bool, str)
    progress_updated = Signal(int, str)  # 进度, 消息

    def __init__(self, operation_type, source_config, target_config=None, sql_file=""):
        super().__init__()
        self.operation_type = operation_type
        self.source_config = source_config
        self.target_config = target_config
        self.sql_file = sql_file

    def run(self):
        """执行同步/迁移任务"""
        try:
            self.log_updated.emit(f"[INFO] 开始执行: {self.operation_type}")

            # 判断是迁移模式还是传统同步模式
            if self.operation_type == '数据库迁移':
                # 使用新的迁移模块
                self._run_migration()
            elif self.operation_type == '导出SQL':
                # 使用新的导出功能
                self._run_export()
            elif self.operation_type == '导入SQL':
                # 使用新的导入功能
                self._run_import()
            else:
                # 使用传统的同步模块(向后兼容)
                self._run_sync()

        except Exception as e:
            error_msg = f"操作失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_updated.emit(f"[ERROR] {error_msg}")
            self.sync_finished.emit(False, error_msg)

    def _run_sync(self):
        """运行传统同步模式"""
        from .db_config import DatabaseConfig

        # 创建 DatabaseConfig 对象
        config = DatabaseConfig(
            host=self.source_config.get('host'),
            port=self.source_config.get('port'),
            username=self.source_config.get('username'),
            password=self.source_config.get('password'),
            database=self.source_config.get('database')
        )

        sync = DatabaseSynchronizer(config)

        if self.operation_type == '远程到本地':
            result = sync.sync_remote_to_local()
        elif self.operation_type == '本地到远程':
            result = sync.sync_local_to_remote()
        elif self.operation_type == '执行SQL':
            if not self.sql_file or not os.path.exists(self.sql_file):
                self.sync_finished.emit(False, "SQL 文件不存在")
                return
            config.sql_file = self.sql_file
            result = sync.execute_sql()
        else:
            result = "未知的操作类型"
            self.sync_finished.emit(False, result)
            return

        self.log_updated.emit(f"[INFO] {result}")
        self.sync_finished.emit(True, result)

    def _run_migration(self):
        """运行数据库迁移"""
        if not self.target_config:
            self.sync_finished.emit(False, "缺少目标数据库配置")
            return

        # 创建迁移对象
        migration = DatabaseMigration(self.source_config, self.target_config)

        # 连接数据库
        if not migration.connect():
            self.sync_finished.emit(False, "数据库连接失败")
            return

        try:
            # 执行迁移
            success = migration.migrate_database(
                drop_target_tables=True,
                convert_types=True,
                progress_callback=lambda p, msg: self.progress_updated.emit(p, msg)
            )

            if success:
                self.log_updated.emit("[INFO] 数据库迁移成功")
                self.sync_finished.emit(True, "数据库迁移成功")
            else:
                self.log_updated.emit("[WARNING] 数据库迁移部分失败")
                self.sync_finished.emit(False, "数据库迁移部分失败")

        finally:
            migration.close()

    def _run_export(self):
        """运行数据库导出"""
        # 创建迁移对象(只需要源配置)
        migration = DatabaseMigration(self.source_config, {})

        # 连接源数据库
        if not migration.source_adapter.connect():
            self.sync_finished.emit(False, "数据库连接失败")
            return

        try:
            # 生成导出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_name = self.source_config.get('database', 'database')
            output_path = f"export_{db_name}_{timestamp}.sql"

            # 执行导出
            success = migration.export_database(
                output_path=output_path,
                include_data=True,
                progress_callback=lambda p, msg: self.progress_updated.emit(p, msg)
            )

            if success:
                self.log_updated.emit(f"[INFO] SQL导出成功: {output_path}")
                self.sync_finished.emit(True, f"SQL导出成功: {output_path}")
            else:
                self.sync_finished.emit(False, "SQL导出失败")

        finally:
            migration.source_adapter.close()

    def _run_import(self):
        """运行数据库导入"""
        if not self.sql_file or not os.path.exists(self.sql_file):
            self.sync_finished.emit(False, "SQL 文件不存在")
            return

        # 创建迁移对象(只需要目标配置)
        migration = DatabaseMigration({}, self.source_config)

        # 连接目标数据库
        if not migration.target_adapter.connect():
            self.sync_finished.emit(False, "数据库连接失败")
            return

        try:
            # 执行导入
            success, errors = migration.import_database(
                sql_file_path=self.sql_file,
                progress_callback=lambda p, msg: self.progress_updated.emit(p, msg)
            )

            if success:
                self.log_updated.emit("[INFO] SQL导入成功")
                self.sync_finished.emit(True, "SQL导入成功")
            else:
                error_msg = f"SQL导入部分失败: {len(errors)} 个错误"
                self.log_updated.emit(f"[WARNING] {error_msg}")
                self.sync_finished.emit(False, error_msg)

        finally:
            migration.target_adapter.close()


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.config_manager = get_config_manager()
        self.sql_file_path = ""

        # 定时任务调度器
        self.task_scheduler = TaskScheduler(self.config_manager, self.on_scheduler_log)

        # 更新管理器
        self.update_manager = UpdateManager(self)
        self.update_config = get_update_config()
        self.current_version = get_current_version()

        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()

        # 加载配置
        QTimer.singleShot(100, self.load_config)

        # 延迟检查更新（启动3秒后）
        QTimer.singleShot(3000, self.auto_check_update)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("数据库备份同步工具")
        self.setMinimumSize(900, 650)
        self.resize(1000, 750)

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

        # 创建Tab Widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建手动同步Tab
        self.create_manual_sync_tab()

        # 创建定时任务Tab
        self.create_scheduled_task_tab()

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

        check_update_action = QAction("检查更新", self)
        check_update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_update_action)

        help_menu.addSeparator()

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_manual_sync_tab(self):
        """创建手动同步/迁移Tab页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(8)
        tab_layout.setContentsMargins(8, 8, 8, 8)

        # 同步模式和按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        control_layout.addWidget(QLabel("操作模式:"))

        self.sync_type_combo = QComboBox()
        self.sync_type_combo.addItems(["数据库迁移", "远程到本地", "本地到远程", "导出SQL", "导入SQL", "执行SQL"])
        self.sync_type_combo.currentTextChanged.connect(self.on_sync_type_changed)
        control_layout.addWidget(self.sync_type_combo)

        self.start_button = QPushButton("开始执行")
        self.start_button.clicked.connect(self.start_sync)
        self.start_button.setMinimumWidth(100)
        control_layout.addWidget(self.start_button)

        tab_layout.addLayout(control_layout)

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
        tab_layout.addWidget(self.sql_frame)

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
        self.progress_bar.setRange(0, 100)  # 0-100%
        log_layout.addWidget(self.progress_bar)

        tab_layout.addWidget(log_group)

        # 添加到Tab
        self.tab_widget.addTab(tab_widget, "手动同步")

    def create_scheduled_task_tab(self):
        """创建定时任务Tab页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(8)
        tab_layout.setContentsMargins(8, 8, 8, 8)

        # 控制按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        self.scheduler_status_label = QLabel("调度器状态: 未启动")
        control_layout.addWidget(self.scheduler_status_label)
        control_layout.addStretch()

        self.start_scheduler_button = QPushButton("启动调度器")
        self.start_scheduler_button.clicked.connect(self.toggle_scheduler)
        self.start_scheduler_button.setMinimumWidth(100)
        control_layout.addWidget(self.start_scheduler_button)

        self.refresh_tasks_button = QPushButton("刷新任务")
        self.refresh_tasks_button.clicked.connect(self.refresh_task_list)
        self.refresh_tasks_button.setMinimumWidth(100)
        control_layout.addWidget(self.refresh_tasks_button)

        tab_layout.addLayout(control_layout)

        # 任务表格
        task_group = QGroupBox("定时任务列表")
        task_layout = QVBoxLayout(task_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_task_button = QPushButton("添加任务")
        self.add_task_button.clicked.connect(self.add_task)
        self.add_task_button.setMinimumWidth(80)
        button_layout.addWidget(self.add_task_button)

        self.edit_task_button = QPushButton("编辑任务")
        self.edit_task_button.clicked.connect(self.edit_task)
        self.edit_task_button.setMinimumWidth(80)
        self.edit_task_button.setEnabled(False)
        button_layout.addWidget(self.edit_task_button)

        self.delete_task_button = QPushButton("删除任务")
        self.delete_task_button.clicked.connect(self.delete_task)
        self.delete_task_button.setMinimumWidth(80)
        self.delete_task_button.setEnabled(False)
        button_layout.addWidget(self.delete_task_button)

        self.run_task_button = QPushButton("立即执行")
        self.run_task_button.clicked.connect(self.run_task_now)
        self.run_task_button.setMinimumWidth(80)
        self.run_task_button.setEnabled(False)
        button_layout.addWidget(self.run_task_button)

        button_layout.addStretch()

        task_layout.addLayout(button_layout)

        # 任务列表表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels([
            "任务名称", "同步类型", "调度类型", "调度配置", "状态",
            "最后运行", "运行状态", "下次运行"
        ])

        # 设置表格属性
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.itemSelectionChanged.connect(self.on_task_selection_changed)

        # 设置列宽
        self.task_table.setColumnWidth(0, 120)  # 任务名称
        self.task_table.setColumnWidth(1, 100)  # 同步类型
        self.task_table.setColumnWidth(2, 80)   # 调度类型
        self.task_table.setColumnWidth(3, 150)  # 调度配置
        self.task_table.setColumnWidth(4, 60)   # 状态
        self.task_table.setColumnWidth(5, 140)  # 最后运行
        self.task_table.setColumnWidth(6, 80)   # 运行状态

        task_layout.addWidget(self.task_table)

        tab_layout.addWidget(task_group)

        # 日志面板
        log_group = QGroupBox("任务日志")
        log_layout = QVBoxLayout(log_group)

        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        log_control_layout.addWidget(QLabel("日志输出:"))
        log_control_layout.addStretch()

        self.clear_task_log_button = QPushButton("清空日志")
        self.clear_task_log_button.clicked.connect(self.clear_task_log)
        self.clear_task_log_button.setMinimumWidth(80)
        log_control_layout.addWidget(self.clear_task_log_button)

        log_layout.addLayout(log_control_layout)

        # 日志文本区域
        self.task_log_output = QTextEdit()
        self.task_log_output.setReadOnly(True)
        self.task_log_output.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.task_log_output)

        tab_layout.addWidget(log_group)

        # 添加到Tab
        self.tab_widget.addTab(tab_widget, "定时任务")

        # 加载任务列表
        QTimer.singleShot(200, self.refresh_task_list)

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
        is_sql_mode = sync_type in ["导入SQL", "执行SQL"]
        self.sql_frame.setVisible(is_sql_mode)

        if not is_sql_mode:
            self.sql_file_path = ""
            self.sql_file_input.clear()

        # 根据操作类型更新按钮文本
        if sync_type == "数据库迁移":
            self.start_button.setText("开始迁移")
        else:
            self.start_button.setText("开始执行")

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
        """开始同步/迁移"""
        sync_type = self.sync_type_combo.currentText()

        if sync_type == "执行SQL" and not self.sql_file_path:
            QMessageBox.warning(self, "警告", "请选择 SQL 文件")
            return

        try:
            # 从配置管理器读取配置
            local_config = self.config_manager.get_local_config()
            remote_config = self.config_manager.get_remote_config()

            # 根据同步类型选择配置
            if sync_type == "数据库迁移":
                source_config = local_config  # 本地作为源
                target_config = remote_config  # 远程作为目标
                self.log_output.append("[INFO] 模式: 数据库迁移")
                self.log_output.append(f"  源数据库: {source_config.get('db_type', 'mysql')} - {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
                self.log_output.append(f"  目标数据库: {target_config.get('db_type', 'mysql')} - {target_config.get('host')}:{target_config.get('port')}/{target_config.get('database')}")
            elif sync_type == "远程到本地":
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
                target_config = None
                self.log_output.append("[INFO] 模式: 导出SQL")
                self.log_output.append(f"  数据库: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
            elif sync_type == "导入SQL":
                source_config = local_config  # 这里用local_config作为目标
                target_config = None
                if not self.sql_file_path:
                    self.log_output.append("[ERROR] 请选择要导入的 SQL 文件")
                    QMessageBox.warning(self, "警告", "请选择要导入的 SQL 文件")
                    return
                self.log_output.append("[INFO] 模式: 导入SQL")
                self.log_output.append(f"  目标: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
                self.log_output.append(f"  文件: {self.sql_file_path}")
            elif sync_type == "执行SQL":
                source_config = local_config
                target_config = None
                self.log_output.append("[INFO] 模式: 执行SQL")
                self.log_output.append(f"  目标: {source_config.get('host')}:{source_config.get('port')}/{source_config.get('database')}")
                self.log_output.append(f"  文件: {self.sql_file_path}")
            else:
                self.log_output.append(f"[ERROR] 未知的操作类型: {sync_type}")
                return

            self.log_output.append("")

            # 验证配置
            if sync_type in ["数据库迁移", "远程到本地", "本地到远程"]:
                # 需要验证源和目标配置
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

            else:
                # 只需要一个配置
                use_config = source_config
                valid, msg = self.config_manager.validate_config(use_config)
                if not valid:
                    self.log_output.append(f"[ERROR] 数据库配置无效: {msg}")
                    QMessageBox.critical(self, "错误", f"数据库配置无效: {msg}")
                    return

            # 开始同步
            self.set_syncing_state(True)

            # 创建并启动工作线程
            self.worker = SyncWorker(sync_type, source_config, target_config, self.sql_file_path)
            self.worker.log_updated.connect(self.on_log_updated)
            self.worker.sync_finished.connect(self.on_sync_finished)
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.start()

        except Exception as e:
            error_msg = f"启动操作失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_output.append(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)

    def on_progress_updated(self, progress: int, message: str):
        """进度更新处理"""
        if self.progress_bar.isVisible():
            self.progress_bar.setValue(progress)
        if message:
            self.log_output.append(f"[PROGRESS] {message}")

    def set_syncing_state(self, syncing):
        """设置同步状态"""
        self.start_button.setEnabled(not syncing)
        self.start_action.setEnabled(not syncing)
        self.sync_type_combo.setEnabled(not syncing)
        self.browse_button.setEnabled(not syncing)

        if syncing:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("正在执行...")
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
            self.status_label.setText("执行完成")
            self.log_output.append(f"\n✓ {message}\n")
        else:
            self.status_label.setText("执行失败")
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
        QMessageBox.about(self,
            "关于 数据库备份同步工具",
            f"<h2>数据库备份同步工具</h2>"
            f"<p><b>版本:</b> {self.current_version}</p>"
            f"<p>基于 PySide6 开发的数据库管理工具</p>"
            f"<p><b>主要功能:</b></p>"
            "<ul>"
            "<li>MySQL数据库备份与同步</li>"
            "<li>SQL文件导入导出</li>"
            "<li>定时任务调度</li>"
            "<li>自动更新检查</li>"
            "</ul>"
            f"<p><b>项目地址:</b> <a href='https://github.com/pengcunfu/DatabaseBackup'>https://github.com/pengcunfu/DatabaseBackup</a></p>"
            "<p>© 2025 Database Backup Tool</p>"
        )

    def check_for_updates(self):
        """检查更新"""
        self.update_manager.check_for_updates(self.current_version)

    def auto_check_update(self):
        """自动检查更新"""
        if self.update_config.should_check_update():
            logger.info("自动检查更新...")
            self.update_manager.check_for_updates(self.current_version)
            self.update_config.update_last_check()

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

        # 停止定时任务调度器
        if self.task_scheduler.is_running():
            self.task_scheduler.stop()

        event.accept()

    # ==================== 定时任务相关方法 ====================

    def toggle_scheduler(self):
        """切换调度器状态"""
        if self.task_scheduler.is_running():
            # 停止调度器
            self.task_scheduler.stop()
            self.start_scheduler_button.setText("启动调度器")
            self.scheduler_status_label.setText("调度器状态: 已停止")
            self.task_log_output.append("[INFO] 调度器已停止")
        else:
            # 启动调度器
            if self.task_scheduler.start():
                self.start_scheduler_button.setText("停止调度器")
                self.scheduler_status_label.setText("调度器状态: 运行中")
                self.task_log_output.append("[INFO] 调度器已启动")
            else:
                QMessageBox.warning(self, "错误", "启动调度器失败,请检查是否安装了 apscheduler")

    def refresh_task_list(self):
        """刷新任务列表"""
        tasks = self.task_scheduler.get_all_tasks()

        self.task_table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # 任务名称
            self.task_table.setItem(row, 0, QTableWidgetItem(task.name))

            # 同步类型
            self.task_table.setItem(row, 1, QTableWidgetItem(task.sync_type))

            # 调度类型
            schedule_type_map = {
                "interval": "间隔",
                "cron": "Cron",
                "once": "一次性"
            }
            self.task_table.setItem(row, 2, QTableWidgetItem(schedule_type_map.get(task.schedule_type, task.schedule_type)))

            # 调度配置
            schedule_config = self._get_schedule_config_display(task)
            self.task_table.setItem(row, 3, QTableWidgetItem(schedule_config))

            # 状态
            status_item = QTableWidgetItem("启用" if task.enabled else "禁用")
            if task.enabled:
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.task_table.setItem(row, 4, status_item)

            # 最后运行时间
            last_run = task.last_run_time.split("T")[1][:8] if task.last_run_time else "从未运行"
            self.task_table.setItem(row, 5, QTableWidgetItem(last_run))

            # 运行状态
            status_text = task.last_run_status if task.last_run_status else "-"
            status_item = QTableWidgetItem(status_text)
            if task.last_run_status == "成功":
                status_item.setForeground(Qt.GlobalColor.green)
            elif task.last_run_status == "失败":
                status_item.setForeground(Qt.GlobalColor.red)
            self.task_table.setItem(row, 6, status_item)

            # 下次运行时间
            next_run = task.next_run_time.split("T")[1][:8] if task.next_run_time else "-"
            self.task_table.setItem(row, 7, QTableWidgetItem(next_run))

    def _get_schedule_config_display(self, task: ScheduledTask) -> str:
        """获取调度配置显示文本"""
        if task.schedule_type == "interval":
            hours = task.interval_seconds // 3600
            minutes = (task.interval_seconds % 3600) // 60
            if hours > 0:
                return f"每 {hours}h {minutes}min"
            else:
                return f"每 {minutes}min"
        elif task.schedule_type == "cron":
            return task.cron_expression
        elif task.schedule_type == "once":
            return task.run_time or "-"
        return "-"

    def on_task_selection_changed(self):
        """任务选择改变时的处理"""
        has_selection = len(self.task_table.selectedItems()) > 0
        self.edit_task_button.setEnabled(has_selection)
        self.delete_task_button.setEnabled(has_selection)
        self.run_task_button.setEnabled(has_selection)

    def add_task(self):
        """添加任务"""
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.Accepted:
            task = dialog.task_data
            success, message = self.task_scheduler.add_task(task)

            if success:
                self.task_log_output.append(f"[SUCCESS] {message}")
                self.refresh_task_list()
            else:
                QMessageBox.warning(self, "添加失败", message)

    def edit_task(self):
        """编辑任务"""
        selected_items = self.task_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        task_name = self.task_table.item(row, 0).text()

        # 获取任务
        task = self.task_scheduler.get_task(task_name)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在")
            return

        # 显示编辑对话框
        dialog = TaskDialog(self, task)
        if dialog.exec() == QDialog.Accepted:
            new_task = dialog.task_data
            success, message = self.task_scheduler.update_task(task_name, new_task)

            if success:
                self.task_log_output.append(f"[SUCCESS] {message}")
                self.refresh_task_list()
            else:
                QMessageBox.warning(self, "更新失败", message)

    def delete_task(self):
        """删除任务"""
        selected_items = self.task_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        task_name = self.task_table.item(row, 0).text()

        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务 '{task_name}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        success, message = self.task_scheduler.delete_task(task_name)

        if success:
            self.task_log_output.append(f"[SUCCESS] {message}")
            self.refresh_task_list()
        else:
            QMessageBox.warning(self, "删除失败", message)

    def run_task_now(self):
        """立即执行任务"""
        selected_items = self.task_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        task_name = self.task_table.item(row, 0).text()

        # 获取任务
        task = self.task_scheduler.get_task(task_name)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在")
            return

        self.task_log_output.append(f"[INFO] 立即执行任务: {task_name}")

        # 在后台线程中执行任务
        import threading
        thread = threading.Thread(target=self.task_scheduler._execute_task, args=(task,))
        thread.start()

    def clear_task_log(self):
        """清空任务日志"""
        self.task_log_output.clear()

    def on_scheduler_log(self, message: str):
        """调度器日志回调"""
        # 在任务日志中输出
        if hasattr(self, 'task_log_output'):
            self.task_log_output.append(message)
            # 自动滚动到底部
            self.task_log_output.verticalScrollBar().setValue(
                self.task_log_output.verticalScrollBar().maximum()
            )


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