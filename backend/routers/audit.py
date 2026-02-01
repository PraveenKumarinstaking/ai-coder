"""
Audit Logs Router - Audit Log Management
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
import models
import schemas
from auth import get_current_user, require_manager_or_admin

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("/", response_model=List[schemas.AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[int] = None,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get audit logs with filters (Manager/Admin only)"""
    query = db.query(models.AuditLog).options(
        joinedload(models.AuditLog.user)
    )
    
    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(models.AuditLog.timestamp >= start_date)
    
    if action:
        query = query.filter(models.AuditLog.action == action)
    if entity_type:
        query = query.filter(models.AuditLog.entity_type == entity_type)
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    
    return query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()


@router.get("/my-activity", response_model=List[schemas.AuditLogResponse])
async def get_my_activity(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current user's activity log"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    return db.query(models.AuditLog).filter(
        models.AuditLog.user_id == current_user.id,
        models.AuditLog.timestamp >= start_date
    ).order_by(models.AuditLog.timestamp.desc()).limit(50).all()


@router.get("/agent-actions", response_model=List[schemas.AuditLogResponse])
async def get_agent_actions(
    agent_name: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get AI agent actions (Manager/Admin only)"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(models.AuditLog).filter(
        models.AuditLog.agent_involved.isnot(None),
        models.AuditLog.timestamp >= start_date
    )
    
    if agent_name:
        query = query.filter(models.AuditLog.agent_involved == agent_name)
    
    return query.order_by(models.AuditLog.timestamp.desc()).limit(100).all()


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get audit log summary (Manager/Admin only)"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= start_date
    ).all()
    
    # Count by action
    actions = {}
    for log in logs:
        actions[log.action] = actions.get(log.action, 0) + 1
    
    # Count by entity type
    entities = {}
    for log in logs:
        entities[log.entity_type] = entities.get(log.entity_type, 0) + 1
    
    # Count agent actions
    agent_actions = 0
    for log in logs:
        if log.agent_involved:
            agent_actions += 1
    
    return {
        "total_actions": len(logs),
        "by_action": actions,
        "by_entity": entities,
        "agent_actions": agent_actions,
        "period_days": days
    }


@router.get("/agents/status", response_model=List[schemas.AgentStatusResponse])
async def get_agent_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get AI agent status (Manager/Admin only)"""
    return db.query(models.AgentStatus).all()
