"""
Planning Agent - Analyzes tasks and calculates priority scores
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Planning Agent responsible for:
    - Calculating priority scores based on urgency and importance
    - Analyzing task dependencies
    - Suggesting optimal scheduling
    """
    
    def __init__(self):
        self.agent_name = "PlanningAgent"
    
    def calculate_priority_score(self, task: models.Task) -> float:
        """
        Calculate priority score (0-100) based on multiple factors:
        - Due date urgency
        - Task priority level
        - Number of dependent tasks
        - Current status
        """
        score = 50.0  # Base score
        
        # 1. Due date urgency (0-30 points)
        if task.due_date:
            now = datetime.utcnow()
            time_remaining = (task.due_date - now).total_seconds() / 3600  # hours
            
            if time_remaining < 0:  # Overdue
                score += 30
            elif time_remaining < 24:  # Due within 24 hours
                score += 25
            elif time_remaining < 48:  # Due within 48 hours
                score += 20
            elif time_remaining < 72:  # Due within 3 days
                score += 15
            elif time_remaining < 168:  # Due within a week
                score += 10
        
        # 2. Priority level (0-25 points)
        priority_weights = {
            models.TaskPriority.CRITICAL: 25,
            models.TaskPriority.HIGH: 20,
            models.TaskPriority.MEDIUM: 10,
            models.TaskPriority.LOW: 5
        }
        score += priority_weights.get(task.priority, 10)
        
        # 3. Dependent tasks (0-15 points)
        # More tasks depending on this one = higher priority
        dependent_count = len(task.dependent_tasks) if hasattr(task, 'dependent_tasks') else 0
        score += min(dependent_count * 5, 15)
        
        # 4. Task age (0-10 points)
        # Older incomplete tasks get higher priority
        if task.created_at:
            age_days = (datetime.utcnow() - task.created_at).days
            score += min(age_days, 10)
        
        # Cap score at 100
        return min(score, 100.0)
    
    def analyze_dependencies(self, task: models.Task, db: Session) -> dict:
        """Analyze task dependencies and identify blockers"""
        result = {
            "has_blockers": False,
            "blocked_by": [],
            "blocking": [],
            "ready_to_start": True
        }
        
        # Check dependencies
        for dep in task.dependencies:
            if dep.status != models.TaskStatus.COMPLETED:
                result["has_blockers"] = True
                result["ready_to_start"] = False
                result["blocked_by"].append({
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status.value
                })
        
        # Check what this task is blocking
        for blocked in task.dependent_tasks:
            result["blocking"].append({
                "id": blocked.id,
                "title": blocked.title
            })
        
        return result
    
    def run(self):
        """Execute planning agent job"""
        logger.info(f"[{self.agent_name}] Starting task analysis...")
        
        db = SessionLocal()
        try:
            # Get all active tasks
            tasks = db.query(models.Task).filter(
                models.Task.status.in_([
                    models.TaskStatus.PENDING,
                    models.TaskStatus.IN_PROGRESS
                ])
            ).all()
            
            updated_count = 0
            for task in tasks:
                old_score = task.priority_score
                new_score = self.calculate_priority_score(task)
                
                if abs(old_score - new_score) > 1:  # Only update if significant change
                    task.priority_score = new_score
                    updated_count += 1
                    
                    # Log significant priority changes
                    if new_score - old_score > 10:
                        audit_log = models.AuditLog(
                            action="priority_increased",
                            entity_type="task",
                            entity_id=task.id,
                            agent_involved=self.agent_name,
                            details=f"Priority score increased from {old_score:.1f} to {new_score:.1f}"
                        )
                        db.add(audit_log)
            
            db.commit()
            
            # Update agent status
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            
            if agent_status:
                agent_status.last_run = datetime.utcnow()
                agent_status.tasks_processed += len(tasks)
                db.commit()
            
            logger.info(f"[{self.agent_name}] Analyzed {len(tasks)} tasks, updated {updated_count} priority scores")
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error: {str(e)}")
            
            # Log error
            agent_status = db.query(models.AgentStatus).filter(
                models.AgentStatus.agent_name == self.agent_name
            ).first()
            if agent_status:
                agent_status.errors_count += 1
                agent_status.last_error = str(e)
                db.commit()
        finally:
            db.close()
