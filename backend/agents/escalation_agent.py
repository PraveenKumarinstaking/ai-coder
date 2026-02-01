"""
Escalation Agent - Handles automatic task escalation
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

logger = logging.getLogger(__name__)


class EscalationAgent:
    """
    Escalation Agent responsible for:
    - Detecting overdue tasks
    - Auto-escalating high-risk tasks to managers
    - Sending escalation notifications
    """
    
    def __init__(self):
        self.agent_name = "EscalationAgent"
        self.escalation_threshold_hours = 0  # Hours past due before escalation
        self.confidence_escalation_threshold = 30.0  # Confidence below this triggers escalation
    
    def should_escalate(self, task: models.Task) -> tuple:
        """
        Determine if a task should be escalated
        Returns: (should_escalate, reason)
        """
        if task.is_escalated:
            return False, None
        
        if task.status == models.TaskStatus.COMPLETED:
            return False, None
        
        # Check if overdue
        if task.due_date and task.due_date < datetime.utcnow():
            hours_overdue = (datetime.utcnow() - task.due_date).total_seconds() / 3600
            if hours_overdue > self.escalation_threshold_hours:
                return True, f"Overdue by {hours_overdue:.1f} hours"
        
        # Check confidence score
        if task.confidence_score < self.confidence_escalation_threshold:
            return True, f"Critically low confidence score ({task.confidence_score:.0f}%)"
        
        # Check if task has been in progress too long without updates
        if task.status == models.TaskStatus.IN_PROGRESS and task.updated_at:
            days_since_update = (datetime.utcnow() - task.updated_at).days
            if days_since_update >= 3:
                return True, f"No progress for {days_since_update} days"
        
        return False, None
    
    def find_manager_to_escalate_to(self, task: models.Task, db: Session) -> models.User:
        """Find an appropriate manager to escalate to"""
        # First, try to find any manager
        manager = db.query(models.User).filter(
            models.User.role == models.UserRole.MANAGER,
            models.User.is_active == True
        ).first()
        
        if not manager:
            # Fall back to admin
            manager = db.query(models.User).filter(
                models.User.role == models.UserRole.ADMIN,
                models.User.is_active == True
            ).first()
        
        return manager
    
    def escalate_task(self, task: models.Task, reason: str, manager: models.User, db: Session):
        """Perform the escalation"""
        task.is_escalated = True
        task.escalated_to = manager.id
        task.status = models.TaskStatus.ESCALATED
        
        # Create notification for manager
        notification = models.Notification(
            type="escalation",
            message=f"🚨 ESCALATED: Task '{task.title}' requires attention. Reason: {reason}",
            channel=models.NotificationChannel.BOTH,
            user_id=manager.id,
            task_id=task.id
        )
        db.add(notification)
        
        # Also notify the assignee
        if task.assigned_to != manager.id:
            assignee_notification = models.Notification(
                type="escalation",
                message=f"📢 Your task '{task.title}' has been escalated to {manager.name}. Reason: {reason}",
                channel=models.NotificationChannel.DESKTOP,
                user_id=task.assigned_to,
                task_id=task.id
            )
            db.add(assignee_notification)
        
        # Log the escalation
        audit_log = models.AuditLog(
            action="task_escalated",
            entity_type="task",
            entity_id=task.id,
            agent_involved=self.agent_name,
            details=f"Task escalated to {manager.name}. Reason: {reason}"
        )
        db.add(audit_log)
    
    def run(self):
        """Execute escalation agent job"""
        logger.info(f"[{self.agent_name}] Starting escalation check...")
        
        db = SessionLocal()
        try:
            # Get active, non-escalated tasks
            tasks = db.query(models.Task).filter(
                models.Task.is_escalated == False,
                models.Task.status.in_([
                    models.TaskStatus.PENDING,
                    models.TaskStatus.IN_PROGRESS,
                    models.TaskStatus.OVERDUE
                ])
            ).all()
            
            escalated_count = 0
            
            for task in tasks:
                should_escalate, reason = self.should_escalate(task)
                
                if should_escalate:
                    manager = self.find_manager_to_escalate_to(task, db)
                    if manager:
                        self.escalate_task(task, reason, manager, db)
                        escalated_count += 1
                        logger.info(f"[{self.agent_name}] Escalated task {task.id}: {task.title}")
            
            db.commit()
            
            # Update agent status
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            
            if agent_status:
                agent_status.last_run = datetime.utcnow()
                agent_status.tasks_processed += len(tasks)
                db.commit()
            
            logger.info(f"[{self.agent_name}] Checked {len(tasks)} tasks, escalated {escalated_count}")
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error: {str(e)}")
            
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            if agent_status:
                agent_status.errors_count += 1
                agent_status.last_error = str(e)
                db.commit()
        finally:
            db.close()
