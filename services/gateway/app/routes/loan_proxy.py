from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.security import get_bearer_token
from app.schemas.loan import LoanCreate, LoanUpdate
from app.services.proxy_service import forward_request


router = APIRouter()


@router.post("/loans")
async def proxy_create_loan(
    payload: LoanCreate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.LOAN_SERVICE_URL}/loans",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.get("/loans")
async def proxy_list_loans(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.LOAN_SERVICE_URL}/loans",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.put("/loans/{loan_id}")
async def proxy_update_loan(
    loan_id: int,
    payload: LoanUpdate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="PUT",
        url=f"{settings.LOAN_SERVICE_URL}/loans/{loan_id}",
        headers=headers,
        json_body=payload.model_dump(mode="json", exclude_none=True),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.delete("/loans/{loan_id}")
async def proxy_delete_loan(
    loan_id: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="DELETE",
        url=f"{settings.LOAN_SERVICE_URL}/loans/{loan_id}",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.get("/loans/health")
async def proxy_loan_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.LOAN_SERVICE_URL}/health",
    )
    return JSONResponse(content=data, status_code=status_code)