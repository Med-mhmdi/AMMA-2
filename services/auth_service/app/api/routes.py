from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth_service import AuthService


router = APIRouter()


@router.get("/health")
def health_check():
    """Simple health endpoint for service monitoring."""
    return {"status": "ok", "service": "auth_service"}


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)

    try:
        user = auth_service.register(payload)
        return user
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)

    try:
        access_token = auth_service.login(payload)
        return TokenResponse(access_token=access_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc