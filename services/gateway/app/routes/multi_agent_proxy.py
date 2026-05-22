from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from pydantic import BaseModel
import httpx

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
    """
    JSON endpoint.

    Used by frontend when image is already converted to base64.
    It forwards the request to multi_agent_system.
    """

    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    status_code, data = await forward_request(
        method="POST",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/analyze",
        headers=headers,
        json_body=payload.model_dump(mode="json"),
        timeout=300.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.post("/agent/analyze/upload")
async def proxy_agent_analyze_upload(
    user_id: int | None = Form(default=None),
    session_id: str | None = Form(default=None),
    message: str | None = Form(default="Analyze this receipt image"),
    image: UploadFile = File(...),
    authorization: str | None = Depends(get_bearer_token),
):
    """
    Swagger-friendly endpoint.

    This gives a real Choose File button in Swagger.
    It forwards the uploaded image to multi_agent_system.
    """

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file.",
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    headers = {}

    if authorization:
        headers["Authorization"] = authorization

    form_data = {}

    if user_id is not None:
        form_data["user_id"] = str(user_id)

    if session_id is not None:
        form_data["session_id"] = session_id

    if message is not None:
        form_data["message"] = message

    files = {
        "image": (
            image.filename or "uploaded_image.png",
            image_bytes,
            image.content_type or "image/png",
        )
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/analyze/upload",
            headers=headers,
            data=form_data,
            files=files,
        )

    try:
        response_data = response.json()
    except Exception:
        response_data = {
            "detail": response.text,
        }

    return JSONResponse(
        content=response_data,
        status_code=response.status_code,
    )


@router.get("/agent/graph/mermaid")
async def proxy_agent_graph_mermaid():
    """
    Returns the improved Mermaid graph as JSON.
    """

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/graph/mermaid",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/agent/graph/mermaid/raw")
async def proxy_agent_graph_mermaid_raw():
    """
    Returns the raw Mermaid graph as plain text.
    Useful for copying directly into Mermaid editors.
    """

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/graph/mermaid/raw"
        )

    return PlainTextResponse(
        content=response.text,
        status_code=response.status_code,
    )


@router.get("/agent/llm/config")
async def proxy_agent_llm_config():
    """
    Returns Ollama model configuration from multi_agent_system.
    """

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/llm/config",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/agent/observability/langfuse")
async def proxy_agent_langfuse_observability():
    """
    Returns Langfuse observability status from multi_agent_system.
    """

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/observability/langfuse",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)


@router.get("/agent/health")
async def proxy_agent_health():
    """
    Returns health status from multi_agent_system.
    """

    status_code, data = await forward_request(
        method="GET",
        url=f"{settings.MULTI_AGENT_SYSTEM_URL}/agent/health",
        headers={},
        timeout=30.0,
    )

    return JSONResponse(content=data, status_code=status_code)