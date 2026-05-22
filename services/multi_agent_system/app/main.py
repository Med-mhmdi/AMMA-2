from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as agent_router
from app.config import settings
from app.observability.langfuse_client import get_langfuse_status, flush_langfuse
from shared.amma_observability import setup_observability


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
setup_observability(app, service_name="amma-agent-service")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agent_service",
        "observability": {
            "langfuse": get_langfuse_status(),
        },
    }


@app.on_event("shutdown")
def shutdown_event():
    flush_langfuse()
