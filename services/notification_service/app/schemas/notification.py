from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)
    type: str = Field(
        pattern="^(budget_alert|loan_reminder|bill_reminder|subscription_reminder|ai_insight|system_message)$"
    )
    status: str = Field(
        default="pending",
        pattern="^(pending|sent|read|dismissed|failed)$"
    )
    related_entity_id: int | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None


class NotificationUpdateStatus(BaseModel):
    status: str = Field(pattern="^(pending|sent|read|dismissed|failed)$")


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    status: str
    related_entity_id: int | None = None
    created_at: datetime | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None

    class Config:
        from_attributes = True