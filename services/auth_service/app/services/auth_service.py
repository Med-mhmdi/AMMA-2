from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.token_service import TokenService


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthService:
    """Business logic layer for authentication operations."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(password, password_hash)

    def register(self, payload: RegisterRequest):
        """Register a new user if the email is not already used."""
        existing_user = self.user_repository.get_by_email(payload.email)
        if existing_user:
            raise ValueError("Email already exists")

        password_hash = self.hash_password(payload.password)

        return self.user_repository.create(
            email=payload.email,
            phone_number=payload.phone_number,
            password_hash=password_hash,
            first_name=payload.first_name,
            family_name=payload.family_name,
        )

    def login(self, payload: LoginRequest) -> str:
        """Authenticate a user and return an access token."""
        user = self.user_repository.get_by_email(payload.email)
        if not user:
            raise ValueError("Invalid credentials")

        if not self.verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid credentials")

        return TokenService.create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
            }
        )