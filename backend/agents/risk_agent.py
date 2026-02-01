"""
Risk Agent - Monitors risk factors and calculates confidence scores
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

logger = logging.getLogger(__name__)


class RiskAgent:
    """
    Risk Agent responsible for:
    - Calculating confidence scores based on risk factors
    - Identifying high-risk tasks
    - Generating risk alerts
    """
    
    def __init__(self):
        self.agent_name = "RiskAgent"
        self.low_confidence_threshold = 40.0
    
    def calculate_confidence_score(self, task: models.Task, db: Session) -> float:
        """
        Calculate confidence score (0-100) based on risk factors:
        - Time remaining vs estimated effort
        - Dependency completion status
        - Historical completion rates
        - Task priority level
        """
        score = 100.0  # Start at full confidence
        
        # 1. Time factor (-0 to -40 points)
        if task.due_date:
            now = datetime.utcnow()
            time_remaining = (task.due_date - now).total_seconds() / 3600  # hours
            
            if time_remaining < 0:  # Overdue
                score -= 40
            elif time_remaining < 8:  # Less than 8 hours
                score -= 30
            elif time_remaining < 24:  # Less than 24 hours
                score -= 20
            elif time_remaining < 48:  # Less than 48 hours
                score -= 10
        
        # 2. Dependency risk (-0 to -30 points)
        incomplete_deps = 0
        for dep in task.dependencies:
            if dep.status != models.TaskStatus.COMPLETED:
                incomplete_deps += 1
                # Check if dependency is also at risk
                if dep.confidence_score < 50:
                    score -= 10  # Extra penalty for risky dependencies
        
        score -= min(incomplete_deps * 10, 30)
        
        # 3. Task complexity/priority risk (-0 to -15 points)
        if task.priority == models.TaskPriority.CRITICAL:
            score -= 10  # Critical tasks are inherently riskier
        elif task.priority == models.TaskPriority.HIGH:
            score -= 5
        
        # 4. Status factor
        if task.status == models.TaskStatus.PENDING:
            # Not started yet - reduce confidence
            if task.due_date:
                days_until_due = (task.due_date - datetime.utcnow()).days
                if days_until_due < 2 and task.priority in [models.TaskPriority.HIGH, models.TaskPriority.CRITICAL]:
                    score -= 15  # High priority not started with little time
        
        # Ensure score stays within bounds
        return max(0.0, min(100.0, score))
    
    def identify_bottlenecks(self, db: Session) -> list:
        """Identify tasks that are blocking multiple other tasks"""
        bottlenecks = []
        
        tasks = db.query(models.Task).filter(
            models.Task.status != models.TaskStatus.COMPLETED
        ).all()
        
        for task in tasks:
            blocked_count = len(task.dependent_tasks)
            if blocked_count >= 2:  # Task is blocking 2+ other tasks
                bottlenecks.append({
                    "task_id": task.id,
                    "title": task.title,
                    "blocking_count": blocked_count,
                    "confidence_score": task.confidence_score,
                    "status": task.status.value
                })
        
        return sorted(bottlenecks, key=lambda x: x["blocking_count"], reverse=True)
    
    def run(self):
        """Execute risk agent job"""
        logger.info(f"[{self.agent_name}] Starting risk assessment...")
        
        db = SessionLocal()
        try:
            # Get all active tasks
            tasks = db.query(models.Task).filter(
                models.Task.status.in_([
                    models.TaskStatus.PENDING,
                    models.TaskStatus.IN_PROGRESS
                ])
            ).all()
            
            high_risk_count = 0
            updated_count = 0
            
            for task in tasks:
                old_score = task.confidence_score
                new_score = self.calculate_confidence_score(task, db)
                
                if abs(old_score - new_score) > 2:  # Only update if significant change
                    task.confidence_score = new_score
                    updated_count += 1
                    
                    # Check if newly high-risk
                    if new_score < self.low_confidence_threshold:
                        high_risk_count += 1
                        
                        # Log the risk detection
                        if old_score >= self.low_confidence_threshold:
                            audit_log = models.AuditLog(
                                action="high_risk_detected",
                                entity_type="task",
                                entity_id=task.id,
                                agent_involved=self.agent_name,
                                details=f"Task '{task.title}' dropped to high-risk status. Confidence: {new_score:.1f}%"
                            )
                            db.add(audit_log)
                            
                            # Create notification for assignee
                            notification = models.Notification(
                                type="alert",
                                message=f"⚠️ Task '{task.title}' has been flagged as HIGH RISK (Confidence: {new_score:.0f}%)",
                                channel=models.NotificationChannel.DESKTOP,
                                user_id=task.assigned_to,
                                task_id=task.id
                            )
                            db.add(notification)
            
            db.commit()
            
            # Update agent status
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            
            if agent_status:
                agent_status.last_run = datetime.utcnow()
                agent_status.tasks_processed += len(tasks)
                db.commit()
            
            logger.info(f"[{self.agent_name}] Assessed {len(tasks)} tasks, updated {updated_count} scores, found {high_risk_count} high-risk")
            
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
