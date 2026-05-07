from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.security import get_bearer_token
from app.services.proxy_service import forward_request


router = APIRouter()


@router.post("/notifications")
async def proxy_create_notification(
    payload: dict,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.NOTIFICATION_SERVICE_URL}/notifications",
        headers=headers,
        json_body=payload,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/notifications")
async def proxy_list_notifications(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.NOTIFICATION_SERVICE_URL}/notifications",
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.patch("/notifications/{notification_id}/status")
async def proxy_update_notification_status(
    notification_id: int,
    payload: dict,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="PATCH",
        url=f"{settings.NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/status",
        headers=headers,
        json_body=payload,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/notifications/health")
async def proxy_notification_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.NOTIFICATION_SERVICE_URL}/health",
    )

    return JSONResponse(content=data, status_code=status_code)