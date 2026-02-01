"""
Scheduler - APScheduler setup for running AI agents periodically
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from agents import PlanningAgent, RiskAgent, EscalationAgent, NotificationAgent

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

# Agent instances
planning_agent = PlanningAgent()
risk_agent = RiskAgent()
escalation_agent = EscalationAgent()
notification_agent = NotificationAgent()


def setup_scheduler():
    """Initialize and start the scheduler with all agent jobs"""
    global scheduler
    
    scheduler = BackgroundScheduler()
    
    # Planning Agent - runs every 5 minutes
    scheduler.add_job(
        planning_agent.run,
        trigger=IntervalTrigger(minutes=5),
        id="planning_agent",
        name="Task Planning Agent",
        replace_existing=True
    )
    
    # Risk Agent - runs every 3 minutes
    scheduler.add_job(
        risk_agent.run,
        trigger=IntervalTrigger(minutes=3),
        id="risk_agent",
        name="Risk Assessment Agent",
        replace_existing=True
    )
    
    # Escalation Agent - runs every 10 minutes
    scheduler.add_job(
        escalation_agent.run,
        trigger=IntervalTrigger(minutes=10),
        id="escalation_agent",
        name="Escalation Agent",
        replace_existing=True
    )
    
    # Notification Agent - runs every 2 minutes
    scheduler.add_job(
        notification_agent.run,
        trigger=IntervalTrigger(minutes=2),
        id="notification_agent",
        name="Notification Agent",
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started with all agents")
    
    # Run agents once at startup
    try:
        planning_agent.run()
        risk_agent.run()
        notification_agent.run()
    except Exception as e:
        logger.error(f"Error running initial agent jobs: {str(e)}")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown complete")


def get_scheduler_status():
    """Get status of all scheduled jobs"""
    if not scheduler:
        return {"status": "not running", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        "status": "running",
        "jobs": jobs
    }


def run_agent_manually(agent_name: str):
    """Run a specific agent manually"""
    agents = {
        "planning": planning_agent,
        "risk": risk_agent,
        "escalation": escalation_agent,
        "notification": notification_agent
    }
    
    agent = agents.get(agent_name.lower())
    if agent:
        agent.run()
        return True
    return False
