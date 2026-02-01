"""
Notification Agent - Manages scheduled notifications and reminders
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

logger = logging.getLogger(__name__)


class NotificationAgent:
    """
    Notification Agent responsible for:
    - Scheduling task reminders
    - Processing pending notifications
    - Handling retry logic for failed notifications
    """
    
    def __init__(self):
        self.agent_name = "NotificationAgent"
        self.reminder_hours = [24, 8, 2]  # Remind at 24h, 8h, and 2h before due
    
    def create_reminder(self, task: models.Task, hours_before: int, db: Session):
        """Create a reminder notification for a task"""
        # Check if reminder already exists
        existing = db.query(models.Notification).filter(
            models.Notification.task_id == task.id,
            models.Notification.type == "reminder",
            models.Notification.message.contains(f"{hours_before} hour")
        ).first()
        
        if existing:
            return None
        
        if hours_before == 1:
            urgency = "🔴 URGENT"
        elif hours_before <= 8:
            urgency = "🟡 WARNING"
        else:
            urgency = "🔔 REMINDER"
        
        notification = models.Notification(
            type="reminder",
            message=f"{urgency}: Task '{task.title}' is due in {hours_before} hours!",
            channel=models.NotificationChannel.DESKTOP,
            user_id=task.assigned_to,
            task_id=task.id,
            scheduled_at=task.due_date - timedelta(hours=hours_before)
        )
        
        return notification
    
    def process_scheduled_notifications(self, db: Session) -> int:
        """Process notifications that are scheduled to be sent"""
        now = datetime.utcnow()
        
        # Find notifications scheduled for now or earlier
        pending = db.query(models.Notification).filter(
            models.Notification.status == models.NotificationStatus.PENDING,
            models.Notification.scheduled_at <= now
        ).all()
        
        sent_count = 0
        for notification in pending:
            try:
                # Simulate sending (in production, would actually send email/desktop notification)
                notification.status = models.NotificationStatus.SENT
                notification.sent_at = now
                sent_count += 1
                
                logger.info(f"[{self.agent_name}] Sent notification {notification.id}: {notification.message[:50]}...")
                
            except Exception as e:
                notification.status = models.NotificationStatus.FAILED
                notification.retry_count += 1
                logger.error(f"[{self.agent_name}] Failed to send notification {notification.id}: {str(e)}")
        
        return sent_count
    
    def retry_failed_notifications(self, db: Session) -> int:
        """Retry sending failed notifications"""
        failed = db.query(models.Notification).filter(
            models.Notification.status == models.NotificationStatus.FAILED,
            models.Notification.retry_count < models.Notification.max_retries
        ).all()
        
        retry_count = 0
        for notification in failed:
            try:
                notification.status = models.NotificationStatus.RETRYING
                
                # Simulate retry (in production, would actually resend)
                notification.status = models.NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                retry_count += 1
                
                # Log successful retry
                audit_log = models.AuditLog(
                    action="notification_retry_success",
                    entity_type="notification",
                    entity_id=notification.id,
                    agent_involved=self.agent_name,
                    details=f"Notification sent after {notification.retry_count} retries"
                )
                db.add(audit_log)
                
            except Exception as e:
                notification.retry_count += 1
                if notification.retry_count >= notification.max_retries:
                    notification.status = models.NotificationStatus.FAILED
                    
                    # Notify about permanent failure
                    audit_log = models.AuditLog(
                        action="notification_permanently_failed",
                        entity_type="notification",
                        entity_id=notification.id,
                        agent_involved=self.agent_name,
                        details=f"Notification failed after {notification.max_retries} retries"
                    )
                    db.add(audit_log)
        
        return retry_count
    
    def schedule_upcoming_reminders(self, db: Session) -> int:
        """Schedule reminders for tasks with upcoming due dates"""
        now = datetime.utcnow()
        reminder_window = now + timedelta(hours=max(self.reminder_hours) + 1)
        
        tasks = db.query(models.Task).filter(
            models.Task.status.in_([
                models.TaskStatus.PENDING,
                models.TaskStatus.IN_PROGRESS
            ]),
            models.Task.due_date > now,
            models.Task.due_date <= reminder_window
        ).all()
        
        created_count = 0
        for task in tasks:
            hours_until_due = (task.due_date - now).total_seconds() / 3600
            
            for reminder_hour in self.reminder_hours:
                if hours_until_due <= reminder_hour and hours_until_due > reminder_hour - 1:
                    notification = self.create_reminder(task, reminder_hour, db)
                    if notification:
                        db.add(notification)
                        created_count += 1
        
        return created_count
    
    def run(self):
        """Execute notification agent job"""
        logger.info(f"[{self.agent_name}] Starting notification processing...")
        
        db = SessionLocal()
        try:
            # Schedule new reminders
            scheduled = self.schedule_upcoming_reminders(db)
            
            # Process pending notifications
            sent = self.process_scheduled_notifications(db)
            
            # Retry failed notifications
            retried = self.retry_failed_notifications(db)
            
            db.commit()
            
            # Update agent status
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            
            if agent_status:
                agent_status.last_run = datetime.utcnow()
                agent_status.tasks_processed += sent + retried
                db.commit()
            
            logger.info(f"[{self.agent_name}] Scheduled {scheduled}, sent {sent}, retried {retried} notifications")
            
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
