from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Repository layer for user database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email if found."""
        return self.db.query(User).filter(User.email == email).first()

    def create(
        self,
        email: str,
        phone_number: str | None,
        password_hash: str,
        first_name: str,
        family_name: str,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            email=email,
            phone_number=phone_number,
            password_hash=password_hash,
            first_name=first_name,
            family_name=family_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user