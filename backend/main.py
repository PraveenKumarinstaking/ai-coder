"""
ERP-Grade Agentic AI Task & Workflow Management System
FastAPI Backend Entry Point
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List

from database import engine, Base, SessionLocal
from routers import users, tasks, notifications, audit
from scheduler import setup_scheduler, shutdown_scheduler, get_scheduler_status, run_agent_manually
import models
from auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from websocket_manager import manager
from sqlalchemy import event
import json
from datetime import datetime


def init_database():
    """Initialize database and create default users"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(models.User).filter(models.User.email == "admin@erp.com").first()
        if not admin:
            # Create default admin user
            admin = models.User(
                email="admin@erp.com",
                password_hash=get_password_hash("admin123"),
                name="System Admin",
                role=models.UserRole.ADMIN
            )
            db.add(admin)
            
            # Create default manager
            manager_user = models.User(
                email="manager@erp.com",
                password_hash=get_password_hash("manager123"),
                name="Project Manager",
                role=models.UserRole.MANAGER
            )
            db.add(manager_user)
            
            # Create default user
            user = models.User(
                email="user@erp.com",
                password_hash=get_password_hash("user123"),
                name="John Developer",
                role=models.UserRole.USER
            )
            db.add(user)
            
            db.commit()
            logger.info("Default users created successfully")
            
            # Create initial agent status records
            agents = ["PlanningAgent", "EscalationAgent", "NotificationAgent", "RiskAgent"]
            for agent_name in agents:
                agent = models.AgentStatus(
                    agent_name=agent_name,
                    status="running"
                )
                db.add(agent)
            db.commit()
            logger.info("Agent status records initialized")
            
    finally:
        db.close()

# SQLAlchemy event listener for real-time audit logs
@event.listens_for(models.AuditLog, 'after_insert')
def audit_log_after_insert(mapper, connection, target):
    """Broadcast new audit logs via WebSocket"""
    # Create serializable dict
    log_data = {
        "id": target.id,
        "action": target.action,
        "details": target.details,
        "entity_type": target.entity_type,
        "entity_id": target.entity_id,
        "timestamp": target.timestamp.isoformat() if target.timestamp else datetime.utcnow().isoformat(),
        "agent_involved": target.agent_involved,
        "user_id": target.user_id,
        # Note: We can't easily join user here without another session, 
        # but the frontend can handle it or we can pass a simple name if available
    }
    
    # Send broadcast
    manager.broadcast_sync({
        "type": "AUDIT_LOG",
        "data": log_data
    })

# SQLAlchemy event listeners for real-time task updates
@event.listens_for(models.Task, 'after_insert')
@event.listens_for(models.Task, 'after_update')
def task_after_change(mapper, connection, target):
    """Broadcast task changes via WebSocket"""
    task_data = {
        "id": target.id,
        "title": target.title,
        "status": target.status,
        "priority": target.priority,
        "due_date": target.due_date.isoformat(),
        "confidence_score": target.confidence_score,
        "assigned_to": target.assigned_to,
        "created_by": target.created_by
    }
    manager.broadcast_sync({
        "type": "TASK_UPDATE",
        "data": task_data
    })

@event.listens_for(models.Task, 'after_delete')
def task_after_delete(mapper, connection, target):
    manager.broadcast_sync({
        "type": "TASK_DELETE",
        "data": {"id": target.id}
    })

# SQLAlchemy event listeners for real-time notification updates
@event.listens_for(models.Notification, 'after_insert')
@event.listens_for(models.Notification, 'after_update')
def notification_after_change(mapper, connection, target):
    """Broadcast notification changes via WebSocket"""
    notification_data = {
        "id": target.id,
        "type": target.type,
        "message": target.message,
        "is_read": target.is_read,
        "user_id": target.user_id,
        "task_id": target.task_id,
        "created_at": target.created_at.isoformat()
    }
    manager.broadcast_sync({
        "type": "NOTIFICATION_UPDATE",
        "data": notification_data
    })

@event.listens_for(models.Notification, 'after_delete')
def notification_after_delete(mapper, connection, target):
    manager.broadcast_sync({
        "type": "NOTIFICATION_DELETE",
        "data": {"id": target.id}
    })


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting ERP Agentic AI System...")
    init_database()
    setup_scheduler()
    logger.info("System ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    shutdown_scheduler()


# Create FastAPI app
app = FastAPI(
    title="ERP-Grade Agentic AI Task System",
    description="Enterprise Task & Workflow Management with AI-powered prioritization, escalation, and risk monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(notifications.router)
app.include_router(audit.router)


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "ERP-Grade Agentic AI Task System",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    scheduler_status = get_scheduler_status()
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": scheduler_status["status"],
        "active_jobs": len(scheduler_status["jobs"])
    }


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get scheduler and agent status"""
    return get_scheduler_status()


@app.post("/api/scheduler/run/{agent_name}")
async def run_agent(agent_name: str):
    """Manually trigger an agent run"""
    success = run_agent_manually(agent_name)
    if success:
        return {"message": f"Agent {agent_name} executed successfully"}
    return {"error": f"Unknown agent: {agent_name}"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can extend for bidirectional communication
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/broadcast")
async def broadcast_message(message: dict):
    """Broadcast message to all WebSocket clients"""
    await manager.broadcast(message)
    return {"status": "broadcast sent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
