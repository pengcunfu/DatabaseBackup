#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务编辑对话框
用于添加和编辑定时任务
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QSpinBox, QDateTimeEdit, QPushButton, QGroupBox,
    QTabWidget, QWidget, QLabel, QMessageBox, QTimeEdit
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont

from .scheduler_config import ScheduledTask


class TaskDialog(QDialog):
    """定时任务编辑对话框"""

    def __init__(self, parent=None, task: Optional[ScheduledTask] = None):
        super().__init__(parent)
        self.task = task
        self.is_edit_mode = task is not None

        self.init_ui()
        if self.is_edit_mode:
            self.load_task_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑定时任务" if self.is_edit_mode else "添加定时任务")
        self.setMinimumSize(500, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入任务名称")
        basic_layout.addRow("任务名称*:", self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        self.description_input.setPlaceholderText("输入任务描述(可选)")
        basic_layout.addRow("任务描述:", self.description_input)

        self.enabled_checkbox = QCheckBox("启用此任务")
        self.enabled_checkbox.setChecked(True)
        basic_layout.addRow("", self.enabled_checkbox)

        layout.addWidget(basic_group)

        # 同步配置
        sync_group = QGroupBox("同步配置")
        sync_layout = QFormLayout(sync_group)

        self.sync_type_combo = QComboBox()
        self.sync_type_combo.addItems(["远程到本地", "本地到远程"])
        sync_layout.addRow("同步类型*:", self.sync_type_combo)

        self.drop_tables_checkbox = QCheckBox("同步前删除目标表")
        sync_layout.addRow("", self.drop_tables_checkbox)

        self.exclude_tables_input = QLineEdit()
        self.exclude_tables_input.setPlaceholderText("例如: user_sessions, login_attempts (用逗号分隔)")
        sync_layout.addRow("排除的表:", self.exclude_tables_input)

        self.include_tables_input = QLineEdit()
        self.include_tables_input.setPlaceholderText("例如: users, orders (用逗号分隔, 留空表示所有表)")
        sync_layout.addRow("包含的表:", self.include_tables_input)

        layout.addWidget(sync_group)

        # 调度配置
        schedule_group = QGroupBox("调度配置")
        schedule_layout = QFormLayout(schedule_group)

        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems(["interval", "cron", "once"])
        self.schedule_type_combo.currentTextChanged.connect(self.on_schedule_type_changed)
        schedule_layout.addRow("调度类型*:", self.schedule_type_combo)

        # 间隔调度
        interval_layout = QHBoxLayout()
        self.interval_hours = QSpinBox()
        self.interval_hours.setRange(0, 8760)
        self.interval_hours.setValue(1)
        self.interval_hours.setSuffix(" 小时")
        interval_layout.addWidget(self.interval_hours)

        self.interval_minutes = QSpinBox()
        self.interval_minutes.setRange(0, 59)
        self.interval_minutes.setValue(0)
        self.interval_minutes.setSuffix(" 分钟")
        interval_layout.addWidget(self.interval_minutes)

        self.interval_seconds = QSpinBox()
        self.interval_seconds.setRange(0, 59)
        self.interval_seconds.setValue(0)
        self.interval_seconds.setSuffix(" 秒")
        interval_layout.addWidget(self.interval_seconds)

        interval_layout.addStretch()
        self.interval_widget = QWidget()
        self.interval_widget.setLayout(interval_layout)
        schedule_layout.addRow("执行间隔:", self.interval_widget)

        # Cron 表达式
        self.cron_input = QLineEdit()
        self.cron_input.setPlaceholderText("分 时 日 月 周 (例如: 0 2 * * * 表示每天凌晨2点)")
        schedule_layout.addRow("Cron 表达式:", self.cron_input)
        self.cron_label = QLabel(self._get_cron_help_text())
        self.cron_label.setWordWrap(True)
        self.cron_label.setStyleSheet("color: gray; font-size: 11px;")
        schedule_layout.addRow("", self.cron_label)

        # 一次性执行时间
        self.run_time_input = QTimeEdit()
        self.run_time_input.setDisplayFormat("HH:mm")
        self.run_time_input.setTime(QDateTime.currentDateTime().time())
        schedule_layout.addRow("执行时间:", self.run_time_input)

        # 初始化显示状态
        self.on_schedule_type_changed(self.schedule_type_combo.currentText())

        layout.addWidget(schedule_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("确定")
        self.ok_button.setMinimumWidth(80)
        self.ok_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _get_cron_help_text(self) -> str:
        """获取Cron表达式帮助文本"""
        return ("格式: 分 时 日 月 周\n"
                "示例: 0 2 * * * (每天凌晨2点)\n"
                "      0 */6 * * * (每6小时)\n"
                "      30 8 * * 1-5 (工作日早上8:30)")

    def on_schedule_type_changed(self, schedule_type: str):
        """调度类型改变时的处理"""
        if schedule_type == "interval":
            self.interval_widget.setVisible(True)
            self.interval_widget.setEnabled(True)
            self.cron_input.setVisible(False)
            self.cron_label.setVisible(False)
            self.run_time_input.setVisible(False)
        elif schedule_type == "cron":
            self.interval_widget.setVisible(False)
            self.cron_input.setVisible(True)
            self.cron_label.setVisible(True)
            self.run_time_input.setVisible(False)
        elif schedule_type == "once":
            self.interval_widget.setVisible(False)
            self.cron_input.setVisible(False)
            self.cron_label.setVisible(False)
            self.run_time_input.setVisible(True)

    def load_task_data(self):
        """加载任务数据"""
        if not self.task:
            return

        self.name_input.setText(self.task.name)
        self.description_input.setText(self.task.description)
        self.enabled_checkbox.setChecked(self.task.enabled)
        self.sync_type_combo.setCurrentText(self.task.sync_type)
        self.drop_tables_checkbox.setChecked(self.task.drop_target_tables)

        if self.task.exclude_tables:
            self.exclude_tables_input.setText(", ".join(self.task.exclude_tables))

        if self.task.include_tables:
            self.include_tables_input.setText(", ".join(self.task.include_tables))

        self.schedule_type_combo.setCurrentText(self.task.schedule_type)

        # 加载间隔时间
        hours = self.task.interval_seconds // 3600
        minutes = (self.task.interval_seconds % 3600) // 60
        seconds = self.task.interval_seconds % 60
        self.interval_hours.setValue(hours)
        self.interval_minutes.setValue(minutes)
        self.interval_seconds.setValue(seconds)

        # 加载Cron表达式
        self.cron_input.setText(self.task.cron_expression)

        # 加载一次性执行时间
        if self.task.run_time:
            time_parts = self.task.run_time.split(":")
            if len(time_parts) == 2:
                from PySide6.QtCore import QTime
                self.run_time_input.setTime(QTime(int(time_parts[0]), int(time_parts[1])))

    def get_task_data(self) -> Optional[ScheduledTask]:
        """获取任务数据"""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        enabled = self.enabled_checkbox.isChecked()
        sync_type = self.sync_type_combo.currentText()
        drop_tables = self.drop_tables_checkbox.isChecked()

        exclude_tables_str = self.exclude_tables_input.text().strip()
        exclude_tables = [t.strip() for t in exclude_tables_str.split(",") if t.strip()] if exclude_tables_str else []

        include_tables_str = self.include_tables_input.text().strip()
        include_tables = [t.strip() for t in include_tables_str.split(",") if t.strip()] if include_tables_str else []

        schedule_type = self.schedule_type_combo.currentText()

        # 计算间隔秒数
        interval_seconds = self.interval_hours.value() * 3600 + \
                          self.interval_minutes.value() * 60 + \
                          self.interval_seconds.value()

        cron_expression = self.cron_input.text().strip()

        # 格式化一次性执行时间
        run_time = None
        if schedule_type == "once":
            time = self.run_time_input.time()
            run_time = f"{time.hour():02d}:{time.minute():02d}"

        # 创建任务对象
        task = ScheduledTask(
            name=name,
            enabled=enabled,
            sync_type=sync_type,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            run_time=run_time,
            exclude_tables=exclude_tables,
            include_tables=include_tables,
            drop_target_tables=drop_tables,
            description=description
        )

        # 如果是编辑模式，保留原有的创建时间和运行状态
        if self.is_edit_mode and self.task:
            task.created_at = self.task.created_at
            task.last_run_time = self.task.last_run_time
            task.last_run_status = self.task.last_run_status

        return task

    def validate_and_accept(self):
        """验证并接受"""
        task = self.get_task_data()

        if not task:
            return

        # 验证任务配置
        valid, msg = task.validate()
        if not valid:
            QMessageBox.warning(self, "验证失败", msg)
            return

        self.task_data = task
        self.accept()
