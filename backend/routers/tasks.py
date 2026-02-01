"""
Tasks Router - Task CRUD and Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
import models
import schemas
from auth import get_current_user, require_manager_or_admin

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/", response_model=schemas.TaskResponse)
async def create_task(
    task_data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new task"""
    # Verify assignee exists
    assignee = db.query(models.User).filter(models.User.id == task_data.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    # Create task
    task = models.Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        assigned_to=task_data.assigned_to,
        created_by=current_user.id,
        confidence_score=100.0,  # Will be calculated by AI agent
        priority_score=50.0
    )
    
    # Add dependencies
    if task_data.dependency_ids:
        dependencies = db.query(models.Task).filter(
            models.Task.id.in_(task_data.dependency_ids)
        ).all()
        task.dependencies = dependencies
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Log the creation
    audit_log = models.AuditLog(
        action="task_created",
        entity_type="task",
        entity_id=task.id,
        user_id=current_user.id,
        details=f"Task '{task.title}' created and assigned to {assignee.name}"
    )
    db.add(audit_log)
    db.commit()
    
    return task


@router.get("/", response_model=List[schemas.TaskResponse])
async def get_all_tasks(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all tasks with optional filters"""
    query = db.query(models.Task).options(
        joinedload(models.Task.assignee),
        joinedload(models.Task.creator)
    )
    
    # Regular users only see their tasks
    if current_user.role == models.UserRole.USER:
        query = query.filter(models.Task.assigned_to == current_user.id)
    
    if status_filter:
        query = query.filter(models.Task.status == status_filter)
    if priority_filter:
        query = query.filter(models.Task.priority == priority_filter)
    
    return query.order_by(models.Task.due_date.asc()).all()


@router.get("/my-tasks", response_model=List[schemas.TaskResponse])
async def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get tasks assigned to current user"""
    return db.query(models.Task).options(
        joinedload(models.Task.assignee),
        joinedload(models.Task.creator)
    ).filter(
        models.Task.assigned_to == current_user.id
    ).order_by(models.Task.due_date.asc()).all()


@router.get("/dashboard-stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get dashboard statistics for current user"""
    base_query = db.query(models.Task)
    
    if current_user.role == models.UserRole.USER:
        base_query = base_query.filter(models.Task.assigned_to == current_user.id)
    
    total = base_query.count()
    in_progress = base_query.filter(models.Task.status == models.TaskStatus.IN_PROGRESS).count()
    completed = base_query.filter(models.Task.status == models.TaskStatus.COMPLETED).count()
    overdue = base_query.filter(
        models.Task.due_date < datetime.utcnow(),
        models.Task.status != models.TaskStatus.COMPLETED
    ).count()
    high_risk = base_query.filter(models.Task.confidence_score < 40).count()
    
    return {
        "total_tasks": total,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "high_risk": high_risk
    }


@router.get("/manager-stats", response_model=schemas.ManagerStats)
async def get_manager_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get manager dashboard statistics"""
    total = db.query(models.Task).count()
    overdue = db.query(models.Task).filter(
        models.Task.due_date < datetime.utcnow(),
        models.Task.status != models.TaskStatus.COMPLETED
    ).count()
    high_risk = db.query(models.Task).filter(models.Task.confidence_score < 40).count()
    
    # Tasks per user
    tasks_per_user = {}
    users = db.query(models.User).filter(models.User.role == models.UserRole.USER).all()
    overloaded_count = 0
    
    for user in users:
        task_count = db.query(models.Task).filter(
            models.Task.assigned_to == user.id,
            models.Task.status != models.TaskStatus.COMPLETED
        ).count()
        tasks_per_user[user.name] = task_count
        if task_count > 5:  # Overloaded threshold
            overloaded_count += 1
    
    # Status distribution
    status_dist = {}
    for status in models.TaskStatus:
        count = db.query(models.Task).filter(models.Task.status == status).count()
        status_dist[status.value] = count
    
    # Completion trend (last 7 days)
    trend = []
    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        completed = db.query(models.Task).filter(
            func.date(models.Task.completed_at) == date.date()
        ).count()
        trend.append({
            "date": date.strftime("%b %d"),
            "completed": completed
        })
    
    return {
        "total_tasks": total,
        "overdue_tasks": overdue,
        "high_risk_tasks": high_risk,
        "overloaded_users": overloaded_count,
        "tasks_per_user": tasks_per_user,
        "status_distribution": status_dist,
        "completion_trend": trend
    }


@router.get("/high-risk", response_model=List[schemas.TaskResponse])
async def get_high_risk_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get high-risk tasks (Manager/Admin only)"""
    return db.query(models.Task).options(
        joinedload(models.Task.assignee)
    ).filter(
        models.Task.confidence_score < 40
    ).order_by(models.Task.confidence_score.asc()).all()


@router.get("/overdue", response_model=List[schemas.TaskResponse])
async def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get overdue tasks (Manager/Admin only)"""
    return db.query(models.Task).options(
        joinedload(models.Task.assignee)
    ).filter(
        models.Task.due_date < datetime.utcnow(),
        models.Task.status != models.TaskStatus.COMPLETED
    ).order_by(models.Task.due_date.asc()).all()


@router.get("/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get task by ID"""
    task = db.query(models.Task).options(
        joinedload(models.Task.assignee),
        joinedload(models.Task.creator),
        joinedload(models.Task.dependencies)
    ).filter(models.Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permission
    if current_user.role == models.UserRole.USER and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update task"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    
    # Log update
    audit_log = models.AuditLog(
        action="task_updated",
        entity_type="task",
        entity_id=task.id,
        user_id=current_user.id,
        details=f"Task '{task.title}' updated"
    )
    db.add(audit_log)
    db.commit()
    
    return task


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: int,
    status_update: schemas.TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update task status"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_status = task.status
    task.status = status_update.status
    
    if status_update.status == models.TaskStatus.COMPLETED:
        task.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Log status change
    audit_log = models.AuditLog(
        action="task_status_changed",
        entity_type="task",
        entity_id=task.id,
        user_id=current_user.id,
        details=f"Task status changed from {old_status.value} to {status_update.status.value}"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Status updated", "new_status": status_update.status.value}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete task"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Only creator or admin can delete
    if current_user.role != models.UserRole.ADMIN and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    title = task.title
    db.delete(task)
    db.commit()
    
    # Log deletion
    audit_log = models.AuditLog(
        action="task_deleted",
        entity_type="task",
        entity_id=task_id,
        user_id=current_user.id,
        details=f"Task '{title}' deleted"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Task deleted successfully"}
