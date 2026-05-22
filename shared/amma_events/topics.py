class Topics:
    USER_CREATED = "user.created"
    EXPENSE_CREATED = "expense.created"
    EXPENSE_UPDATED = "expense.updated"
    EXPENSE_DELETED = "expense.deleted"
    BUDGET_UPDATED = "budget.updated"
    LOAN_CREATED = "loan.created"
    LOAN_UPDATED = "loan.updated"
    LOAN_DELETED = "loan.deleted"
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    AI_INSIGHT_GENERATED = "ai.insight.generated"
    ANALYTICS_SNAPSHOT_CREATED = "analytics.snapshot.created"

    DLQ_SUFFIX = ".dlq"

    @classmethod
    def all_business_topics(cls) -> list[str]:
        return [
            cls.USER_CREATED,
            cls.EXPENSE_CREATED,
            cls.EXPENSE_UPDATED,
            cls.EXPENSE_DELETED,
            cls.BUDGET_UPDATED,
            cls.LOAN_CREATED,
            cls.LOAN_UPDATED,
            cls.LOAN_DELETED,
            cls.NOTIFICATION_CREATED,
            cls.NOTIFICATION_SENT,
            cls.AI_INSIGHT_GENERATED,
            cls.ANALYTICS_SNAPSHOT_CREATED,
        ]

    @classmethod
    def all_dead_letter_topics(cls) -> list[str]:
        return [f"{topic}{cls.DLQ_SUFFIX}" for topic in cls.all_business_topics()]
