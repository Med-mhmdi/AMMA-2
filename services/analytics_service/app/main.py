from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes import router
from app.config import settings
from app.consumers.expense_consumer import start_analytics_consumer
from shared.amma_observability import setup_observability


app = FastAPI(title=settings.APP_NAME)
app.include_router(router)
setup_observability(app, service_name="amma-analytics-service")


@app.on_event("startup")
def startup_event():
    start_analytics_consumer()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="AMMA Analytics Service API",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if operation.get("operationId") != "health_check_health_get":
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
