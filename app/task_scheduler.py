#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器模块
使用 APScheduler 实现定时任务的调度和执行
"""

import logging
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    APScheduler_AVAILABLE = True
except ImportError:
    APScheduler_AVAILABLE = False
    BackgroundScheduler = None

from .scheduler_config import ScheduledTask, ScheduledTaskManager
from .db_sync import DatabaseSynchronizer
from .db_config import DatabaseConfig

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self, config_manager, on_log_callback: Optional[Callable] = None):
        """
        初始化调度器

        Args:
            config_manager: 配置管理器实例
            on_log_callback: 日志回调函数
        """
        self.config_manager = config_manager
        self.on_log_callback = on_log_callback

        # 任务配置管理器
        self.task_manager = ScheduledTaskManager()

        # APScheduler 调度器
        self.scheduler: Optional[BackgroundScheduler] = None

        # 初始化调度器
        if APScheduler_AVAILABLE:
            self._init_scheduler()
        else:
            self.log("[WARNING] APScheduler 未安装，定时任务功能不可用")
            self.log("[INFO] 请运行: pip install apscheduler")

    def _init_scheduler(self):
        """初始化 APScheduler"""
        try:
            self.scheduler = BackgroundScheduler()

            # 添加事件监听器
            self.scheduler.add_listener(
                self._on_job_executed,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )

            logger.info("定时任务调度器初始化成功")
        except Exception as e:
            logger.error(f"定时任务调度器初始化失败: {e}", exc_info=True)
            self.scheduler = None

    def start(self):
        """启动调度器"""
        if not self.scheduler:
            self.log("[WARNING] 调度器未初始化，无法启动")
            return False

        if self.scheduler.running:
            self.log("[INFO] 调度器已在运行中")
            return True

        try:
            # 加载并注册所有启用的任务
            self._register_all_tasks()

            # 启动调度器
            self.scheduler.start()
            self.log("[INFO] 定时任务调度器已启动")
            return True
        except Exception as e:
            error_msg = f"启动调度器失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log(f"[ERROR] {error_msg}")
            return False

    def stop(self):
        """停止调度器"""
        if not self.scheduler:
            return

        if not self.scheduler.running:
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.log("[INFO] 定时任务调度器已停止")
        except Exception as e:
            error_msg = f"停止调度器失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log(f"[ERROR] {error_msg}")

    def is_running(self) -> bool:
        """检查调度器是否在运行"""
        return self.scheduler is not None and self.scheduler.running

    def _register_all_tasks(self):
        """注册所有启用的任务"""
        if not self.scheduler:
            return

        # 清除所有现有任务
        self.scheduler.remove_all_jobs()

        # 获取所有启用的任务
        enabled_tasks = self.task_manager.get_enabled_tasks()

        for task in enabled_tasks:
            self._register_task(task)

        if enabled_tasks:
            self.log(f"[INFO] 已注册 {len(enabled_tasks)} 个定时任务")
        else:
            self.log("[INFO] 没有启用的定时任务")

    def _register_task(self, task: ScheduledTask):
        """注册单个任务"""
        if not self.scheduler:
            return

        try:
            # 移除已存在的同名任务
            if self.scheduler.get_job(task.name):
                self.scheduler.remove_job(task.name)

            # 创建触发器
            trigger = self._create_trigger(task)
            if not trigger:
                return

            # 添加任务
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                id=task.name,
                name=task.name,
                args=[task],
                replace_existing=True
            )

            # 更新下次运行时间
            job = self.scheduler.get_job(task.name)
            if job and job.next_run_time:
                task.next_run_time = job.next_run_time.isoformat()
                self.task_manager.save_tasks()

            logger.info(f"任务已注册: {task.name}")
            self.log(f"[INFO] 任务已注册: {task.get_display_info()}")

        except Exception as e:
            error_msg = f"注册任务失败 [{task.name}]: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log(f"[ERROR] {error_msg}")

    def _create_trigger(self, task: ScheduledTask):
        """根据任务配置创建触发器"""
        try:
            if task.schedule_type == "interval":
                # 间隔触发器
                return IntervalTrigger(seconds=task.interval_seconds)

            elif task.schedule_type == "cron":
                # Cron 触发器
                # 解析 cron 表达式 (分 时 日 月 周)
                parts = task.cron_expression.strip().split()
                if len(parts) != 5:
                    self.log(f"[ERROR] Cron 表达式格式错误: {task.cron_expression}")
                    return None

                minute, hour, day, month, day_of_week = parts
                return CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )

            elif task.schedule_type == "once":
                # 一次性触发器
                if not task.run_time:
                    return None

                # 解析运行时间 "HH:MM"
                try:
                    time_parts = task.run_time.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])

                    # 创建今天的运行时间
                    run_date = datetime.now().replace(
                        hour=hour,
                        minute=minute,
                        second=0,
                        microsecond=0
                    )

                    # 如果时间已过，设置为明天
                    if run_date < datetime.now():
                        from datetime import timedelta
                        run_date = run_date + timedelta(days=1)

                    return DateTrigger(run_date=run_date)

                except Exception as e:
                    self.log(f"[ERROR] 解析运行时间失败: {e}")
                    return None

            else:
                self.log(f"[ERROR] 未知的调度类型: {task.schedule_type}")
                return None

        except Exception as e:
            self.log(f"[ERROR] 创建触发器失败: {e}")
            return None

    def _execute_task(self, task: ScheduledTask):
        """执行定时任务"""
        task_name = task.name
        self.log(f"[INFO] 开始执行定时任务: {task_name}")

        try:
            # 获取数据库配置
            if task.sync_type == "远程到本地":
                source_config = self.config_manager.get_remote_config()
                target_config = self.config_manager.get_local_config()
            else:  # 本地到远程
                source_config = self.config_manager.get_local_config()
                target_config = self.config_manager.get_remote_config()

            if not source_config or not target_config:
                error_msg = "数据库配置不完整，无法执行任务"
                self.log(f"[ERROR] {error_msg}")
                self.task_manager.update_task_run_status(task_name, "失败", datetime.now().isoformat())
                return

            # 创建数据库配置对象
            db_config = DatabaseConfig(
                host=source_config.get('host'),
                port=source_config.get('port'),
                username=source_config.get('username'),
                password=source_config.get('password'),
                database=source_config.get('database')
            )

            # 设置同步选项
            db_config.exclude_tables = task.exclude_tables
            db_config.include_tables = task.include_tables
            db_config.drop_target_tables = task.drop_target_tables

            # 创建同步器并执行同步
            sync = DatabaseSynchronizer(db_config)

            if task.sync_type == "远程到本地":
                result = sync.sync_remote_to_local()
            else:  # 本地到远程
                result = sync.sync_local_to_remote()

            # 更新任务状态
            self.task_manager.update_task_run_status(task_name, "成功", datetime.now().isoformat())
            self.log(f"[SUCCESS] 定时任务完成: {task_name}")
            self.log(f"[INFO] {result}")

            # 如果是一次性任务，执行后禁用
            if task.schedule_type == "once":
                task.enabled = False
                self.task_manager.save_tasks()
                self.log(f"[INFO] 一次性任务已执行并禁用: {task_name}")
                if self.scheduler and self.scheduler.get_job(task_name):
                    self.scheduler.remove_job(task_name)

        except Exception as e:
            error_msg = f"执行定时任务失败 [{task_name}]: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log(f"[ERROR] {error_msg}")
            self.task_manager.update_task_run_status(task_name, "失败", datetime.now().isoformat())

    def _on_job_executed(self, event):
        """任务执行事件回调"""
        if event.exception:
            logger.error(f"任务执行异常: {event.job_id}", exc_info=event.exception)
        else:
            logger.info(f"任务执行成功: {event.job_id}")

    def reload_tasks(self):
        """重新加载所有任务"""
        if not self.scheduler:
            return

        self.task_manager.load_tasks()
        self._register_all_tasks()

    def add_task(self, task: ScheduledTask) -> tuple[bool, str]:
        """添加任务"""
        success, message = self.task_manager.add_task(task)
        if success:
            # 如果任务已启用，注册到调度器
            if task.enabled and self.scheduler and self.scheduler.running:
                self._register_task(task)
        return success, message

    def update_task(self, task_name: str, task: ScheduledTask) -> tuple[bool, str]:
        """更新任务"""
        success, message = self.task_manager.update_task(task_name, task)
        if success:
            # 如果调度器正在运行，重新注册任务
            if self.scheduler and self.scheduler.running:
                # 先移除旧任务
                if self.scheduler.get_job(task_name):
                    self.scheduler.remove_job(task_name)
                # 如果任务已启用，重新注册
                if task.enabled:
                    self._register_task(task)
        return success, message

    def delete_task(self, task_name: str) -> tuple[bool, str]:
        """删除任务"""
        success, message = self.task_manager.delete_task(task_name)
        if success:
            # 从调度器中移除
            if self.scheduler and self.scheduler.get_job(task_name):
                self.scheduler.remove_job(task_name)
                self.log(f"[INFO] 任务已从调度器中移除: {task_name}")
        return success, message

    def get_all_tasks(self):
        """获取所有任务"""
        return self.task_manager.get_all_tasks()

    def get_task(self, task_name: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.task_manager.get_task(task_name)

    def log(self, message: str):
        """记录日志"""
        if self.on_log_callback:
            self.on_log_callback(message)
        logger.info(message)
