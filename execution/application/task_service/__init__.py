"""
execution/application/task_service — 任务服务

提供 TaskService 给 infrastructure.task_manager 使用。
"""
from execution.application.task_service.service import TaskService

__all__ = ["TaskService"]
