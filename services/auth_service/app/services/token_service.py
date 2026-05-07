from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


class TokenService:
    """Service responsible for JWT token generation."""

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create a signed JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )