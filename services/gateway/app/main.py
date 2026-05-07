from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.routes.auth_proxy import router as auth_router
from app.routes.expense_proxy import router as expense_router
from app.routes.loan_proxy import router as loan_router
from app.routes.analytics_proxy import router as analytics_router
from app.routes.notification_proxy import router as notification_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title=settings.APP_NAME)

app.include_router(auth_router)
app.include_router(expense_router)
app.include_router(loan_router)
app.include_router(analytics_router)
app.include_router(notification_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.101:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def gateway_health():
    return {"status": "ok", "service": "gateway"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="AMMA API Gateway",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    protected_paths = {
        "/expenses": {"get", "post"},
        "/expenses/{expense_id}": {"put", "delete"},
        "/expenses/summary": {"get"},

        "/categories": {"get", "post"},
        "/categories/{category_id}": {"put", "delete"},

        "/budgets": {"get", "put"},

        "/loans": {"get", "post"},
        "/loans/{loan_id}": {"put", "delete"},

        "/analytics/dashboard": {"get"},
        "/analytics/categories": {"get"},
        "/analytics/daily": {"get"},
        "/analytics/forecast": {"get"},
        "/analytics/cache/invalidate": {"post"},

        "/notifications": {"get", "post"},
        "/notifications/{notification_id}/status": {"patch"},
    }

    for path, methods in openapi_schema["paths"].items():
        if path in protected_paths:
            for method, operation in methods.items():
                if method in protected_paths[path]:
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
