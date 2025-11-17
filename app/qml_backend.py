#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QML 后端桥接类
连接 QML 前端和 Python 业务逻辑
"""

import os
import logging
from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtWidgets import QFileDialog

from .db_config import DatabaseConfig
from .db_sync import DatabaseSynchronizer

logger = logging.getLogger(__name__)


class SyncWorker(QThread):
    """后台同步工作线程"""
    log_updated = Signal(str)
    sync_finished = Signal(bool, str)

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


class QMLBackend(QObject):
    """QML 后端桥接类"""
    
    # 定义信号
    logUpdated = Signal(str)
    statusChanged = Signal(str)
    syncStarted = Signal()
    syncFinished = Signal(bool, str)
    sqlFileSelected = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    @Slot(str, str, int, str, str, str, str)
    def startSync(self, sync_type, host, port, username, password, database, sql_file=""):
        """开始同步"""
        try:
            # 验证输入
            if not host or not username or not database:
                self.logUpdated.emit("[ERROR] 请填写完整的数据库配置信息")
                self.syncFinished.emit(False, "配置信息不完整")
                return
            
            # 创建数据库配置
            config = DatabaseConfig(
                host=host,
                port=port,
                username=username,
                password=password,
                database=database
            )
            
            self.logUpdated.emit(f"[INFO] 配置信息:")
            self.logUpdated.emit(f"  主机: {host}:{port}")
            self.logUpdated.emit(f"  用户: {username}")
            self.logUpdated.emit(f"  数据库: {database}")
            self.logUpdated.emit("")
            
            # 发送开始信号
            self.syncStarted.emit()
            self.statusChanged.emit("正在同步...")
            
            # 创建并启动工作线程
            self.worker = SyncWorker(sync_type, config, sql_file)
            self.worker.log_updated.connect(self.logUpdated)
            self.worker.sync_finished.connect(self._onSyncFinished)
            self.worker.start()
            
        except Exception as e:
            error_msg = f"启动同步失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.logUpdated.emit(f"[ERROR] {error_msg}")
            self.syncFinished.emit(False, error_msg)

    def _onSyncFinished(self, success, message):
        """同步完成回调"""
        self.syncFinished.emit(success, message)
        if success:
            self.statusChanged.emit("同步完成")
        else:
            self.statusChanged.emit("同步失败")

    @Slot()
    def selectSqlFile(self):
        """选择 SQL 文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "选择 SQL 文件",
                "",
                "SQL Files (*.sql);;All Files (*)"
            )
            
            if file_path:
                self.sqlFileSelected.emit(file_path)
                self.logUpdated.emit(f"[INFO] 已选择 SQL 文件: {file_path}")
                
        except Exception as e:
            error_msg = f"选择文件失败: {str(e)}"
            logger.error(error_msg)
            self.logUpdated.emit(f"[ERROR] {error_msg}")

    @Slot()
    def testConnection(self):
        """测试数据库连接"""
        self.logUpdated.emit("[INFO] 测试连接功能待实现")
        self.statusChanged.emit("测试连接...")
