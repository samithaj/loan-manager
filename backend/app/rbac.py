from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from typing import Any

from .auth import PUBLIC_PEM
from .config import get_settings


def _bearer(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


async def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("access_token") or _bearer(request.headers.get("authorization"))
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            PUBLIC_PEM,
            algorithms=["RS256"],
            audience=getattr(settings, "jwt_audience", "loan-manager"),
            issuer=getattr(settings, "jwt_issuer", "http://localhost:8000/auth"),
        )
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
    user = {
        "username": payload.get("uname") or payload.get("sub"),
        "roles": list(payload.get("roles", [])),
        "sub": payload.get("sub"),
    }
    request.state.principal = {"username": user["username"], "roles": user["roles"]}
    return user


def require_roles(*needed: str):
    needed_set = set(needed)

    async def _dep(user=Depends(get_current_user)):
        if not needed_set.intersection(set(user.get("roles", []))):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


