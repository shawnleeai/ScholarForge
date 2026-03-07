"""
Collaboration Task Service
协同任务服务 - 任务管理、协作推送、日程管理
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .models import (
    CollaborationTask, TaskType, TaskPriority, TaskStatus, AssignmentType,
    TaskComment, TaskPush, PaperCollaboration, CollaborationSchedule, WorkloadStats
)


class CollaborationTaskService:
    """协同任务服务"""

    def __init__(self):
        self._tasks: Dict[str, CollaborationTask] = {}
        self._comments: Dict[str, List[TaskComment]] = {}
        self._pushes: Dict[str, List[TaskPush]] = {}
        self._paper_collabs: Dict[str, PaperCollaboration] = {}
        self._schedules: Dict[str, CollaborationSchedule] = {}
        self._workload_stats: Dict[str, WorkloadStats] = {}

    # ==================== 任务管理 ====================

    def create_task(
        self,
        title: str,
        description: str,
        task_type: TaskType,
        creator_id: str,
        **kwargs
    ) -> CollaborationTask:
        """创建任务"""
        task = CollaborationTask(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            task_type=task_type,
            creator_id=creator_id,
            **kwargs
        )

        self._tasks[task.id] = task

        # 发送创建通知
        if task.assignee_id:
            self._create_push(
                task_id=task.id,
                user_id=task.assignee_id,
                push_type="assign",
                title=f"新任务分配: {title}",
                content=f"您被分配了任务: {description[:100]}..."
            )

        return task

    def get_task(self, task_id: str) -> Optional[CollaborationTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        updater_id: str,
        **updates
    ) -> Optional[CollaborationTask]:
        """更新任务"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        old_assignee = task.assignee_id
        old_status = task.status

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # 发送状态变更通知
        if "status" in updates and updates["status"] != old_status:
            self._notify_status_change(task, updater_id, old_status)

        # 发送分配变更通知
        if "assignee_id" in updates and updates["assignee_id"] != old_assignee:
            if updates["assignee_id"]:
                self._create_push(
                    task_id=task.id,
                    user_id=updates["assignee_id"],
                    push_type="assign",
                    title=f"任务分配: {task.title}",
                    content=f"您被分配了新任务"
                )

        return task

    def _notify_status_change(
        self,
        task: CollaborationTask,
        changer_id: str,
        old_status: TaskStatus
    ):
        """通知状态变更"""
        # 通知创建者
        if task.creator_id != changer_id:
            self._create_push(
                task_id=task.id,
                user_id=task.creator_id,
                push_type="update",
                title=f"任务状态更新: {task.title}",
                content=f"状态从 {old_status.value} 变为 {task.status.value}"
            )

        # 通知负责人
        if task.assignee_id and task.assignee_id != changer_id:
            self._create_push(
                task_id=task.id,
                user_id=task.assignee_id,
                push_type="update",
                title=f"任务状态更新: {task.title}",
                content=f"状态从 {old_status.value} 变为 {task.status.value}"
            )

    def list_tasks(
        self,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        paper_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 50
    ) -> List[CollaborationTask]:
        """列出任务"""
        tasks = list(self._tasks.values())

        if user_id:
            tasks = [
                t for t in tasks
                if t.creator_id == user_id or
                t.assignee_id == user_id or
                user_id in t.participants
            ]

        if team_id:
            tasks = [t for t in tasks if t.team_id == team_id]

        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        if paper_id:
            tasks = [t for t in tasks if t.paper_id == paper_id]

        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]

        # 按优先级和截止日期排序
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        tasks.sort(key=lambda x: (
            priority_order.get(x.priority, 2),
            x.due_date or datetime.max
        ))

        return tasks[:limit]

    def get_user_tasks(self, user_id: str) -> Dict[str, List[CollaborationTask]]:
        """获取用户的任务"""
        all_tasks = [
            t for t in self._tasks.values()
            if t.creator_id == user_id or
            t.assignee_id == user_id or
            user_id in t.participants
        ]

        return {
            "assigned": [t for t in all_tasks if t.assignee_id == user_id and t.status != TaskStatus.DONE],
            "created": [t for t in all_tasks if t.creator_id == user_id],
            "participating": [t for t in all_tasks if user_id in t.participants],
            "completed": [t for t in all_tasks if t.assignee_id == user_id and t.status == TaskStatus.DONE]
        }

    def add_task_comment(
        self,
        task_id: str,
        author_id: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> TaskComment:
        """添加任务评论"""
        comment = TaskComment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            author_id=author_id,
            content=content,
            parent_id=parent_id
        )

        if task_id not in self._comments:
            self._comments[task_id] = []

        self._comments[task_id].append(comment)

        # 解析@提及并发送通知
        import re
        mentions = re.findall(r'@(\w+)', content)
        comment.mentions = mentions

        task = self._tasks.get(task_id)
        if task:
            for mention in mentions:
                if mention != author_id:
                    self._create_push(
                        task_id=task_id,
                        user_id=mention,
                        push_type="mention",
                        title=f"您在任务中被提及",
                        content=f"{content[:100]}..."
                    )

        return comment

    # ==================== 推送通知 ====================

    def _create_push(
        self,
        task_id: str,
        user_id: str,
        push_type: str,
        title: str,
        content: str,
        channels: Optional[List[str]] = None
    ) -> TaskPush:
        """创建推送"""
        push = TaskPush(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user_id=user_id,
            push_type=push_type,
            title=title,
            content=content,
            channels=channels or ["app", "email"]
        )

        if user_id not in self._pushes:
            self._pushes[user_id] = []

        self._pushes[user_id].append(push)

        return push

    def get_user_pushes(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[TaskPush]:
        """获取用户推送"""
        pushes = self._pushes.get(user_id, [])

        if unread_only:
            pushes = [p for p in pushes if not p.is_read]

        pushes.sort(key=lambda x: x.created_at, reverse=True)
        return pushes[:limit]

    def mark_push_read(self, push_id: str, user_id: str) -> bool:
        """标记推送已读"""
        pushes = self._pushes.get(user_id, [])

        for push in pushes:
            if push.id == push_id:
                push.is_read = True
                push.read_at = datetime.utcnow()
                return True

        return False

    def check_and_send_reminders(self):
        """检查并发送提醒"""
        now = datetime.utcnow()

        for task in self._tasks.values():
            if task.status in [TaskStatus.DONE, TaskStatus.CANCELLED]:
                continue

            if not task.due_date:
                continue

            # 即将到期提醒（24小时前）
            time_to_due = task.due_date - now

            if timedelta(hours=0) < time_to_due <= timedelta(hours=24):
                if task.assignee_id:
                    self._create_push(
                        task_id=task.id,
                        user_id=task.assignee_id,
                        push_type="due",
                        title=f"任务即将到期: {task.title}",
                        content=f"截止时间是 {task.due_date.isoformat()}"
                    )

            # 已逾期提醒
            elif time_to_due < timedelta(hours=0):
                if task.assignee_id:
                    self._create_push(
                        task_id=task.id,
                        user_id=task.assignee_id,
                        push_type="overdue",
                        title=f"任务已逾期: {task.title}",
                        content=f"原定截止时间 {task.due_date.isoformat()}"
                    )

                # 通知创建者
                if task.creator_id != task.assignee_id:
                    self._create_push(
                        task_id=task.id,
                        user_id=task.creator_id,
                        push_type="overdue",
                        title=f"分配的任务已逾期: {task.title}",
                        content=f"负责人: {task.assignee_id}"
                    )

    # ==================== 论文协作 ====================

    def create_paper_collaboration(
        self,
        paper_id: str,
        lead_author: str,
        **kwargs
    ) -> PaperCollaboration:
        """创建论文协作"""
        collab = PaperCollaboration(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            lead_author=lead_author,
            **kwargs
        )

        self._paper_collabs[collab.id] = collab
        return collab

    def get_paper_collaboration(self, collab_id: str) -> Optional[PaperCollaboration]:
        """获取论文协作"""
        return self._paper_collabs.get(collab_id)

    def add_paper_collaborator(
        self,
        collab_id: str,
        user_id: str,
        role: str  # co_author/reviewer/viewer
    ) -> Optional[PaperCollaboration]:
        """添加论文协作者"""
        collab = self._paper_collabs.get(collab_id)
        if not collab:
            return None

        if role == "co_author":
            if user_id not in collab.co_authors:
                collab.co_authors.append(user_id)
                collab.can_edit.append(user_id)
                collab.can_comment.append(user_id)
        elif role == "reviewer":
            if user_id not in collab.reviewers:
                collab.reviewers.append(user_id)
                collab.can_comment.append(user_id)
        else:  # viewer
            collab.can_view.append(user_id)

        return collab

    # ==================== 日程管理 ====================

    def create_schedule(
        self,
        title: str,
        description: str,
        schedule_type: str,
        organizer_id: str,
        **kwargs
    ) -> CollaborationSchedule:
        """创建日程"""
        schedule = CollaborationSchedule(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            schedule_type=schedule_type,
            organizer_id=organizer_id,
            **kwargs
        )

        self._schedules[schedule.id] = schedule

        # 发送邀请
        for attendee in schedule.attendees:
            self._create_push(
                task_id="",
                user_id=attendee,
                push_type="schedule",
                title=f"日程邀请: {title}",
                content=f"{schedule.start_time.isoformat()} - {description[:100]}"
            )

        return schedule

    def get_schedules(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CollaborationSchedule]:
        """获取用户日程"""
        schedules = []

        for schedule in self._schedules.values():
            if schedule.organizer_id == user_id or user_id in schedule.attendees:
                # 日期过滤
                if start_date and schedule.start_time < start_date:
                    continue
                if end_date and schedule.start_time > end_date:
                    continue
                schedules.append(schedule)

        schedules.sort(key=lambda x: x.start_time)
        return schedules

    # ==================== 工作负载 ====================

    def get_workload_stats(self, user_id: str, team_id: Optional[str] = None) -> WorkloadStats:
        """获取工作负载统计"""
        key = f"{user_id}:{team_id or 'all'}"

        if key in self._workload_stats:
            return self._workload_stats[key]

        # 计算统计
        user_tasks = [
            t for t in self._tasks.values()
            if t.assignee_id == user_id and
            (not team_id or t.team_id == team_id)
        ]

        stats = WorkloadStats(
            user_id=user_id,
            team_id=team_id
        )

        stats.total_tasks = len(user_tasks)
        stats.todo_count = len([t for t in user_tasks if t.status == TaskStatus.TODO])
        stats.in_progress_count = len([t for t in user_tasks if t.status == TaskStatus.IN_PROGRESS])
        stats.review_count = len([t for t in user_tasks if t.status == TaskStatus.REVIEW])
        stats.done_count = len([t for t in user_tasks if t.status == TaskStatus.DONE])

        stats.total_estimated_hours = sum(
            t.estimated_hours or 0 for t in user_tasks
        )
        stats.total_actual_hours = sum(t.actual_hours for t in user_tasks)

        # 时间分布
        now = datetime.utcnow()
        week_end = now + timedelta(days=7)
        next_week_end = now + timedelta(days=14)

        stats.tasks_due_this_week = len([
            t for t in user_tasks
            if t.due_date and now <= t.due_date <= week_end
        ])
        stats.tasks_due_next_week = len([
            t for t in user_tasks
            if t.due_date and week_end < t.due_date <= next_week_end
        ])
        stats.overdue_tasks = len([
            t for t in user_tasks
            if t.due_date and t.due_date < now and t.status != TaskStatus.DONE
        ])

        # 效率统计
        completed_tasks = [t for t in user_tasks if t.status == TaskStatus.DONE]
        if completed_tasks:
            on_time = len([
                t for t in completed_tasks
                if t.due_date and t.completed_at and t.completed_at <= t.due_date
            ])
            stats.completion_rate = stats.done_count / stats.total_tasks
            stats.on_time_rate = on_time / len(completed_tasks)

        self._workload_stats[key] = stats
        return stats


# 单例
_collab_task_service = None


def get_collaboration_task_service() -> CollaborationTaskService:
    """获取协同任务服务单例"""
    global _collab_task_service
    if _collab_task_service is None:
        _collab_task_service = CollaborationTaskService()
    return _collab_task_service
