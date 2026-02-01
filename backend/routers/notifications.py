"""
Notifications Router - Notification Management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# Import manager from main (circular import handling)
# To avoid circular imports, we'll try to import manager inside the function or assume it's passed/available
# Ideally, manager should be in a separate file, but for now we'll write to DB and rely on periodic polling or client refresh
# The main.py has the manager instance.


@router.post("/send-to-all")
async def send_to_all(
    data: schemas.NotificationBroadcast,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send a notification to all users or a specific user"""
    # Allow all authenticated users to send messages (as requested)
    # if current_user.role not in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
    #     raise HTTPException(status_code=403, detail="Not authorized to broadcast messages")
        
    users = []
    if data.recipient_email:
        # Send to specific user
        user = db.query(models.User).filter(models.User.email == data.recipient_email).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with email {data.recipient_email} not found")
        users = [user]
    else:
        # Send to all users
        users = db.query(models.User).filter(models.User.is_active == True).all()
    
    count = 0
    for user in users:
        notification = models.Notification(
            user_id=user.id,
            type=data.type,
            message=f"{data.message}\n\nFrom: {current_user.name} ({current_user.email})",
            channel=data.channel,
            status=models.NotificationStatus.PENDING
        )
        db.add(notification)
        count += 1
        
    db.commit()
    
    target_msg = f"user {data.recipient_email}" if data.recipient_email else f"{count} users"
    return {"message": f"Message sent to {target_msg}"}


@router.get("/", response_model=List[schemas.NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get notifications for current user"""
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    )
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(models.Notification.created_at.desc()).limit(50).all()


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.post("/mark-read")
async def mark_notifications_read(
    data: schemas.NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark notifications as read"""
    db.query(models.Notification).filter(
        models.Notification.id.in_(data.notification_ids),
        models.Notification.user_id == current_user.id
    ).update({models.Notification.is_read: True}, synchronize_session=False)
    
    db.commit()
    
    return {"message": "Notifications marked as read"}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({models.Notification.is_read: True}, synchronize_session=False)
    
    db.commit()
    
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}


@router.get("/stats")
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get notification statistics"""
    total = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).count()
    
    unread = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).count()
    
    by_type = {}
    for notification in db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).all():
        by_type[notification.type] = by_type.get(notification.type, 0) + 1
    
    return {
        "total": total,
        "unread": unread,
        "by_type": by_type
    }
