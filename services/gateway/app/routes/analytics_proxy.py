from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.security import get_bearer_token
from app.services.proxy_service import forward_request


router = APIRouter()


@router.get("/analytics/dashboard")
async def proxy_dashboard(
    year: int,
    month: int,
    period: str,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=(
            f"{settings.ANALYTICS_SERVICE_URL}/analytics/dashboard"
            f"?year={year}&month={month}&period={period}"
        ),
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/analytics/categories")
async def proxy_categories(
    year: int,
    month: int,
    period: str,
    transaction_type: str,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=(
            f"{settings.ANALYTICS_SERVICE_URL}/analytics/categories"
            f"?year={year}&month={month}&period={period}&transaction_type={transaction_type}"
        ),
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/analytics/daily")
async def proxy_daily(
    year: int,
    month: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.ANALYTICS_SERVICE_URL}/analytics/daily?year={year}&month={month}",
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.post("/analytics/cache/invalidate")
async def proxy_invalidate_cache(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.ANALYTICS_SERVICE_URL}/analytics/cache/invalidate",
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)

@router.get("/analytics/forecast")
async def proxy_forecast(
    year: int,
    month: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.ANALYTICS_SERVICE_URL}/analytics/forecast?year={year}&month={month}",
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)

@router.get("/analytics/health")
async def proxy_analytics_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.ANALYTICS_SERVICE_URL}/analytics/health",
    )

    return JSONResponse(content=data, status_code=status_code)