import httpx


async def forward_request(
    method: str,
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    json_body: dict | list | None = None,
):
    """
    Forward an HTTP request to a downstream microservice.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
        )

        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.status_code, response.json()

        return response.status_code, {"detail": response.text}