from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query

from app.core.security import get_current_user
from app.services.chart_service import ChartService
from app.services.summary_service import SummaryService
from app.services.forecast_service import ForecastService


router = APIRouter()


def extract_token(authorization: str | None) -> str:
    if not authorization:
        return ""

    return authorization.replace("Bearer ", "")


@router.get("/analytics/health")
def health_check():
    return {"status": "ok", "service": "analytics_service"}


@router.get("/analytics/dashboard")
async def get_dashboard(
    year: int | None = None,
    month: int | None = None,
    period: str = Query(default="monthly", pattern="^(monthly|yearly)$"),
    current_user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    now = datetime.now()
    selected_year = year or now.year
    selected_month = month or now.month

    token = extract_token(authorization)
    service = SummaryService()

    return await service.build_dashboard_summary(
        user_id=current_user["user_id"],
        token=token,
        year=selected_year,
        month=selected_month,
        period=period,
    )


@router.get("/analytics/categories")
async def get_categories(
    year: int | None = None,
    month: int | None = None,
    period: str = Query(default="monthly", pattern="^(monthly|yearly)$"),
    transaction_type: str = Query(default="outcome", pattern="^(income|outcome)$"),
    current_user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    now = datetime.now()
    selected_year = year or now.year
    selected_month = month or now.month

    token = extract_token(authorization)
    summary_service = SummaryService()
    chart_service = ChartService()

    return await summary_service.build_category_breakdown(
        user_id=current_user["user_id"],
        token=token,
        year=selected_year,
        month=selected_month,
        period=period,
        transaction_type=transaction_type,
        chart_service=chart_service,
    )


@router.get("/analytics/daily")
async def get_daily(
    year: int | None = None,
    month: int | None = None,
    current_user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    now = datetime.now()
    selected_year = year or now.year
    selected_month = month or now.month

    token = extract_token(authorization)
    service = SummaryService()

    return await service.build_daily_summary(
        user_id=current_user["user_id"],
        token=token,
        year=selected_year,
        month=selected_month,
    )

@router.get("/analytics/forecast")
async def get_forecast(
    year: int | None = None,
    month: int | None = None,
    current_user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    now = datetime.now()
    selected_year = year or now.year
    selected_month = month or now.month

    token = extract_token(authorization)

    summary_service = SummaryService()
    forecast_service = ForecastService()

    expenses = await summary_service.get_expense_list(token)
    budget_data = await summary_service.get_budget(token, selected_year, selected_month)

    budget_amount = float(budget_data.get("amount", 0))

    return forecast_service.build_month_forecast(
        expenses=expenses,
        year=selected_year,
        month=selected_month,
        budget=budget_amount,
    )

@router.post("/analytics/cache/invalidate")
def invalidate_cache(current_user=Depends(get_current_user)):
    service = SummaryService()
    service.invalidate_user_cache(current_user["user_id"])

    return {"message": "Analytics cache invalidated"}