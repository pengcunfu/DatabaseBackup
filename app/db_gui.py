#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Tool - GUI Module
Graphical user interface for database synchronization tool
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, 
    QComboBox, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon

from .db_config import DatabaseConfig
from .db_sync import DatabaseSynchronizer

class DatabaseSyncWorker(QThread):
    """后台同步工作线程"""
    sync_progress = Signal(str)
    sync_complete = Signal(bool, str)

    def __init__(self, config, sync_type):
        super().__init__()
        self.config = config
        self.sync_type = sync_type

    def run(self):
        try:
            sync = DatabaseSynchronizer(self.config)
            
            if self.sync_type == '远程到本地':
                result = sync.sync_remote_to_local()
            elif self.sync_type == '本地到远程':
                result = sync.sync_local_to_remote()
            elif self.sync_type == '导出SQL':
                result = sync.export_sql()
            elif self.sync_type == '执行SQL':
                result = sync.execute_sql()
            
            self.sync_complete.emit(True, result)
        except Exception as e:
            self.sync_complete.emit(False, str(e))

class DatabaseSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('数据库同步工具')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:disabled {
                background-color: #a6a6a6;
            }
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        
        self.config = DatabaseConfig()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # 数据库同步页面
        sync_tab = QWidget()
        sync_layout = QVBoxLayout()
        sync_tab.setLayout(sync_layout)
        tab_widget.addTab(sync_tab, "数据库同步")

        # 同步类型选择
        sync_type_layout = QHBoxLayout()
        sync_type_label = QLabel("同步类型:")
        self.sync_type_combo = QComboBox()
        self.sync_type_combo.addItems([
            '远程到本地', 
            '本地到远程', 
            '导出SQL', 
            '执行SQL'
        ])
        sync_type_layout.addWidget(sync_type_label)
        sync_type_layout.addWidget(self.sync_type_combo)
        sync_layout.addLayout(sync_type_layout)

        # 配置输入区域
        config_layout = QVBoxLayout()
        
        # 数据库配置输入
        config_inputs = [
            ('主机', 'host', 'localhost'),
            ('端口', 'port', 3306),
            ('用户名', 'user', 'root'),
            ('密码', 'password', ''),
            ('数据库名', 'database', '')
        ]

        for label_text, config_key, default_value in config_inputs:
            input_layout = QHBoxLayout()
            label = QLabel(label_text + ":")
            input_field = QLineEdit()
            input_field.setText(str(getattr(self.config, config_key, default_value)))
            
            if 'password' in config_key:
                input_field.setEchoMode(QLineEdit.Password)
            
            input_layout.addWidget(label)
            input_layout.addWidget(input_field)
            config_layout.addLayout(input_layout)
            
            # 动态绑定属性
            setattr(self, f'{config_key}_input', input_field)

        sync_layout.addLayout(config_layout)

        # 同步按钮
        sync_button = QPushButton("开始同步")
        sync_button.clicked.connect(self.start_sync)
        sync_layout.addWidget(sync_button)

        # 日志输出区域
        log_label = QLabel("同步日志:")
        sync_layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        sync_layout.addWidget(self.log_output)

        # SQL文件选择（用于执行SQL）
        sql_file_layout = QHBoxLayout()
        sql_file_label = QLabel("SQL文件:")
        self.sql_file_input = QLineEdit()
        sql_file_button = QPushButton("选择文件")
        sql_file_button.clicked.connect(self.select_sql_file)
        
        sql_file_layout.addWidget(sql_file_label)
        sql_file_layout.addWidget(self.sql_file_input)
        sql_file_layout.addWidget(sql_file_button)
        sync_layout.addLayout(sql_file_layout)

    def select_sql_file(self):
        """选择SQL文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择SQL文件", 
            "", 
            "SQL Files (*.sql);;All Files (*)"
        )
        if file_path:
            self.sql_file_input.setText(file_path)

    def start_sync(self):
        """开始同步过程"""
        # 更新配置
        config_attrs = [
            'host', 'port', 
            'user', 'password', 
            'database'
        ]
        
        for attr in config_attrs:
            input_field = getattr(self, f'{attr}_input')
            setattr(self.config, attr, input_field.text())

        # 准备同步配置
        sync_type = self.sync_type_combo.currentText()
        
        # 如果是执行SQL，需要检查SQL文件
        if sync_type == '执行SQL':
            sql_file = self.sql_file_input.text()
            if not sql_file or not os.path.exists(sql_file):
                QMessageBox.warning(self, "错误", "请选择有效的SQL文件")
                return
            self.config.sql_file = sql_file

        # 创建后台工作线程
        self.worker = DatabaseSyncWorker(self.config, sync_type)
        self.worker.sync_progress.connect(self.update_log)
        self.worker.sync_complete.connect(self.sync_finished)
        
        # 禁用同步按钮，防止重复点击
        self.sender().setEnabled(False)
        self.log_output.clear()
        self.worker.start()

    def update_log(self, message):
        """更新日志输出"""
        self.log_output.append(message)

    def sync_finished(self, success, result):
        """同步完成处理"""
        self.sender().setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", result)
        else:
            QMessageBox.warning(self, "错误", result)

def main():
    app = QApplication(sys.argv)
    window = DatabaseSyncApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 