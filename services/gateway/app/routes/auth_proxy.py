from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.proxy_service import forward_request
from app.schemas.auth import LoginRequest, RegisterRequest


router = APIRouter()


@router.post("/auth/register")
async def proxy_register(payload: RegisterRequest):
    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.AUTH_SERVICE_URL}/auth/register",
        json_body=payload.model_dump(),
    )

    return JSONResponse(content=data, status_code=status_code)


@router.post("/auth/login")
async def proxy_login(payload: LoginRequest):
    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.AUTH_SERVICE_URL}/auth/login",
        json_body=payload.model_dump(),
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/auth/health")
async def proxy_auth_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.AUTH_SERVICE_URL}/health",
    )

    return JSONResponse(content=data, status_code=status_code)