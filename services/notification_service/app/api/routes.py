from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationOut,
    NotificationUpdateStatus,
)
from app.services.notification_service import NotificationService


router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "notification_service"}


@router.post("/notifications", response_model=NotificationOut, status_code=201)
def create_notification(
    payload: NotificationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = NotificationRepository(db)
    service = NotificationService(repository)

    return service.create_notification(current_user["user_id"], payload)


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = NotificationRepository(db)
    service = NotificationService(repository)

    return service.list_notifications(current_user["user_id"])


@router.patch("/notifications/{notification_id}/status", response_model=NotificationOut)
def update_notification_status(
    notification_id: int,
    payload: NotificationUpdateStatus,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = NotificationRepository(db)
    service = NotificationService(repository)

    return service.update_status(
        user_id=current_user["user_id"],
        notification_id=notification_id,
        status=payload.status,
    )