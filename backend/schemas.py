"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from models import UserRole, TaskStatus, TaskPriority, NotificationChannel, NotificationStatus


# ========== User Schemas ==========
class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.USER


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ========== Task Schemas ==========
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_date: datetime


class TaskCreate(TaskBase):
    assigned_to: int
    dependency_ids: Optional[List[int]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    confidence_score: float
    priority_score: float
    is_escalated: bool
    assigned_to: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None
    creator: Optional[UserResponse] = None
    dependencies: Optional[List["TaskResponse"]] = []
    
    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


# ========== Notification Schemas ==========
class NotificationBase(BaseModel):
    type: str
    message: str
    channel: Optional[NotificationChannel] = NotificationChannel.DESKTOP


class NotificationCreate(NotificationBase):
    user_id: int
    task_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    id: int
    status: NotificationStatus
    retry_count: int
    is_read: bool
    user_id: int
    task_id: Optional[int] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationBroadcast(NotificationBase):
    recipient_email: Optional[str] = None


class NotificationMarkRead(BaseModel):
    notification_ids: List[int]


# ========== Audit Log Schemas ==========
class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    agent_involved: Optional[str] = None
    user_id: Optional[int] = None
    timestamp: datetime
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


# ========== Agent Status Schemas ==========
class AgentStatusResponse(BaseModel):
    id: int
    agent_name: str
    status: str
    last_run: Optional[datetime] = None
    tasks_processed: int
    errors_count: int
    last_error: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== Dashboard Stats Schemas ==========
class DashboardStats(BaseModel):
    total_tasks: int
    in_progress: int
    completed: int
    overdue: int
    high_risk: int  # Low confidence tasks


class ManagerStats(BaseModel):
    total_tasks: int
    overdue_tasks: int
    high_risk_tasks: int
    overloaded_users: int
    tasks_per_user: dict
    status_distribution: dict
    completion_trend: List[dict]


# Fix circular reference
TaskResponse.model_rebuild()
