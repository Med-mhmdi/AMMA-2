from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.security import get_bearer_token
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.proxy_service import forward_request
from pydantic import BaseModel, Field

router = APIRouter()

class BudgetUpsert(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: int = Field(ge=0)


@router.get("/expenses/health")
async def proxy_expense_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.EXPENSE_SERVICE_URL}/health",
        headers={},
    )
    return JSONResponse(content=data, status_code=status_code)

@router.post("/expenses")
async def proxy_create_expense(
    payload: ExpenseCreate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.EXPENSE_SERVICE_URL}/expenses",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.get("/expenses")
async def proxy_list_expenses(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.EXPENSE_SERVICE_URL}/expenses",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.put("/expenses/{expense_id}")
async def proxy_update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="PUT",
        url=f"{settings.EXPENSE_SERVICE_URL}/expenses/{expense_id}",
        headers=headers,
        json_body=payload.model_dump(mode="json", exclude_none=True),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.delete("/expenses/{expense_id}")
async def proxy_delete_expense(
    expense_id: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="DELETE",
        url=f"{settings.EXPENSE_SERVICE_URL}/expenses/{expense_id}",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.get("/expenses/summary")
async def proxy_expense_summary(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.EXPENSE_SERVICE_URL}/expenses/summary",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.post("/categories")
async def proxy_create_category(
    payload: CategoryCreate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.EXPENSE_SERVICE_URL}/categories",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.get("/categories")
async def proxy_list_categories(
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.EXPENSE_SERVICE_URL}/categories",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)


@router.put("/categories/{category_id}")
async def proxy_update_category(
    category_id: int,
    payload: CategoryUpdate,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="PUT",
        url=f"{settings.EXPENSE_SERVICE_URL}/categories/{category_id}",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
    )
    return JSONResponse(content=data, status_code=status_code)


@router.delete("/categories/{category_id}")
async def proxy_delete_category(
    category_id: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="DELETE",
        url=f"{settings.EXPENSE_SERVICE_URL}/categories/{category_id}",
        headers=headers,
    )
    return JSONResponse(content=data, status_code=status_code)

@router.get("/budgets")
async def proxy_get_budget(
    year: int,
    month: int,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.EXPENSE_SERVICE_URL}/budgets?year={year}&month={month}",
        headers=headers,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.put("/budgets")
async def proxy_upsert_budget(
    payload: BudgetUpsert,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="PUT",
        url=f"{settings.EXPENSE_SERVICE_URL}/budgets",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
    )

    return JSONResponse(content=data, status_code=status_code)
