from fastapi import HTTPException, status

from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Business logic layer for notification operations."""

    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    def create_notification(self, user_id: int, payload: NotificationCreate):
        return self.notification_repository.create(
            user_id=user_id,
            title=payload.title,
            message=payload.message,
            type_=payload.type,
            status=payload.status,
            related_entity_id=payload.related_entity_id,
            scheduled_at=payload.scheduled_at,
            sent_at=payload.sent_at,
        )

    def list_notifications(self, user_id: int):
        return self.notification_repository.list_by_user(user_id)

    def update_status(self, user_id: int, notification_id: int, status: str):
        notification = self.notification_repository.get_by_id(notification_id)

        if not notification or notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return self.notification_repository.update_status(notification, status)