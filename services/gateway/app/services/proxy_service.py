import httpx


async def forward_request(
    method: str,
    url: str,
    headers: dict | None = None,
    json_body: dict | None = None,
    timeout: float = 30.0,
):
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
        )

    try:
        data = response.json()
    except Exception:
        data = {"detail": response.text}

    return response.status_code, data