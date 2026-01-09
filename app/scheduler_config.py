#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务配置模块
定义定时任务的数据模型和配置管理
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ScheduledTask:
    """定时任务配置类"""

    name: str  # 任务名称
    enabled: bool = True  # 是否启用
    sync_type: str = "远程到本地"  # 同步类型: 远程到本地, 本地到远程
    schedule_type: str = "interval"  # 调度类型: interval(间隔), cron(定时), once(一次性)
    interval_seconds: int = 3600  # 间隔秒数 (schedule_type=interval时使用)
    cron_expression: str = ""  # cron表达式 (schedule_type=cron时使用)
    run_time: Optional[str] = None  # 执行时间 "HH:MM" (schedule_type=once时使用)
    exclude_tables: List[str] = field(default_factory=list)  # 排除的表
    include_tables: List[str] = field(default_factory=list)  # 包含的表
    drop_target_tables: bool = False  # 是否删除目标表
    description: str = ""  # 任务描述
    last_run_time: Optional[str] = None  # 最后运行时间
    last_run_status: Optional[str] = None  # 最后运行状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    next_run_time: Optional[str] = None  # 下次运行时间

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledTask':
        """从字典创建实例"""
        return cls(**data)

    def validate(self) -> tuple[bool, str]:
        """验证任务配置是否有效"""
        if not self.name or not self.name.strip():
            return False, "任务名称不能为空"

        if self.sync_type not in ["远程到本地", "本地到远程"]:
            return False, "同步类型必须是: 远程到本地 或 本地到远程"

        if self.schedule_type == "interval":
            if self.interval_seconds <= 0:
                return False, "间隔时间必须大于0"
        elif self.schedule_type == "cron":
            if not self.cron_expression or not self.cron_expression.strip():
                return False, "cron表达式不能为空"
        elif self.schedule_type == "once":
            if not self.run_time:
                return False, "一次性任务必须指定执行时间"
        else:
            return False, "调度类型必须是: interval, cron 或 once"

        return True, ""

    def get_display_info(self) -> str:
        """获取任务显示信息"""
        if self.schedule_type == "interval":
            hours = self.interval_seconds // 3600
            minutes = (self.interval_seconds % 3600) // 60
            if hours > 0:
                schedule_info = f"每 {hours} 小时" + (f" {minutes} 分钟" if minutes > 0 else "")
            elif minutes > 0:
                schedule_info = f"每 {minutes} 分钟"
            else:
                schedule_info = f"每 {self.interval_seconds} 秒"
        elif self.schedule_type == "cron":
            schedule_info = f"Cron: {self.cron_expression}"
        elif self.schedule_type == "once":
            schedule_info = f"一次性: {self.run_time}"
        else:
            schedule_info = "未知调度类型"

        return f"{self.name} - {schedule_info}"


class ScheduledTaskManager:
    """定时任务管理器"""

    def __init__(self, config_file: str = "scheduled_tasks.json"):
        self.config_file = Path(config_file)
        self.tasks: List[ScheduledTask] = []
        self.load_tasks()

    def load_tasks(self):
        """从文件加载任务"""
        if not self.config_file.exists():
            self.tasks = []
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = [ScheduledTask.from_dict(task_data) for task_data in data]
        except Exception as e:
            print(f"加载定时任务配置失败: {e}")
            self.tasks = []

    def save_tasks(self):
        """保存任务到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump([task.to_dict() for task in self.tasks], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存定时任务配置失败: {e}")
            return False

    def add_task(self, task: ScheduledTask) -> tuple[bool, str]:
        """添加任务"""
        # 检查任务名称是否已存在
        if any(t.name == task.name for t in self.tasks):
            return False, "任务名称已存在"

        # 验证任务配置
        valid, msg = task.validate()
        if not valid:
            return False, msg

        self.tasks.append(task)
        if self.save_tasks():
            return True, "任务添加成功"
        return False, "保存失败"

    def update_task(self, task_name: str, task: ScheduledTask) -> tuple[bool, str]:
        """更新任务"""
        # 检查任务名称是否存在
        for i, t in enumerate(self.tasks):
            if t.name == task_name:
                # 验证任务配置
                valid, msg = task.validate()
                if not valid:
                    return False, msg

                self.tasks[i] = task
                if self.save_tasks():
                    return True, "任务更新成功"
                return False, "保存失败"

        return False, "任务不存在"

    def delete_task(self, task_name: str) -> tuple[bool, str]:
        """删除任务"""
        for i, task in enumerate(self.tasks):
            if task.name == task_name:
                self.tasks.pop(i)
                if self.save_tasks():
                    return True, "任务删除成功"
                return False, "保存失败"

        return False, "任务不存在"

    def get_task(self, task_name: str) -> Optional[ScheduledTask]:
        """获取任务"""
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None

    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        return self.tasks.copy()

    def get_enabled_tasks(self) -> List[ScheduledTask]:
        """获取所有启用的任务"""
        return [task for task in self.tasks if task.enabled]

    def update_task_run_status(self, task_name: str, status: str, run_time: str = None):
        """更新任务运行状态"""
        task = self.get_task(task_name)
        if task:
            task.last_run_time = run_time or datetime.now().isoformat()
            task.last_run_status = status
            self.save_tasks()
