from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from app.config import settings
from app.core.security import get_bearer_token
from app.services.proxy_service import forward_request


router = APIRouter()


class AgentAnalyzeRequest(BaseModel):
    user_id: int | None = None
    session_id: str | None = None
    message: str | None = None
    image_base64: str | None = None
    image_url: str | None = None


@router.post("/agent/analyze")
async def proxy_agent_analyze(
    payload: AgentAnalyzeRequest,
    authorization: str | None = Depends(get_bearer_token),
):
    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/analyze",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
        timeout=180.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/agent/graph/mermaid")
async def proxy_agent_graph_mermaid():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/graph/mermaid",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/agent/health")
async def proxy_agent_health():
    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/health",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)