from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Extract Authorization header in Bearer format for proxy forwarding."""
    if not credentials:
        return None

    return f"Bearer {credentials.credentials}"