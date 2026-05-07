from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    """Repository layer for notification database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        title: str,
        message: str,
        type_: str,
        status: str,
        related_entity_id: int | None,
        scheduled_at,
        sent_at,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type_,
            status=status,
            related_entity_id=related_entity_id,
            scheduled_at=scheduled_at,
            sent_at=sent_at,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_by_user(self, user_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def get_by_id(self, notification_id: int) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def update_status(self, notification: Notification, status: str) -> Notification:
        notification.status = status
        self.db.commit()
        self.db.refresh(notification)
        return notification