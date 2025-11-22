from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import PUBLIC_PEM
from .config import get_settings
from .db import get_db
from .models.user import User


def _bearer(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


# Role constants
ROLE_ADMIN = "admin"
ROLE_BRANCH_MANAGER = "branch_manager"
ROLE_SALES_AGENT = "sales_agent"
ROLE_INVENTORY_MANAGER = "inventory_manager"
ROLE_FINANCE_OFFICER = "finance_officer"
ROLE_CUSTOMER_SERVICE = "customer_service"
ROLE_AUDITOR = "auditor"
ROLE_LOAN_MANAGEMENT_OFFICER = "loan_management_officer"  # LMO - creates applications
ROLE_LOAN_OFFICER = "loan_officer"  # LO - approves/rejects applications

# Role permissions mapping
ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: ["*"],  # Admin has all permissions
    ROLE_BRANCH_MANAGER: [
        "bicycles:read",
        "bicycles:write",
        "bicycles:delete",
        "applications:read",
        "applications:write",
        "applications:approve",
        "loans:read",
        "loans:write",
        "clients:read",
        "clients:write",
        "reports:view",
        # HR permissions
        "leaves:read",
        "leaves:approve",
        "attendance:read",
        "attendance:write",
        "bonuses:read",
        "bonuses:approve",
    ],
    ROLE_SALES_AGENT: [
        "applications:read",
        "applications:write",
        "applications:approve",
        "clients:read",
        "clients:write",
        "loans:read",
        "loans:write",
        "bicycles:read",
        # HR permissions
        "attendance:read",
    ],
    ROLE_INVENTORY_MANAGER: [
        "bicycles:read",
        "bicycles:write",
        "bicycles:delete",
        "documents:read",
        "documents:write",
    ],
    ROLE_FINANCE_OFFICER: [
        "loans:read",
        "loans:write",
        "loans:approve",
        "applications:read",
        "clients:read",
        "reports:view",
        # HR permissions
        "bonuses:read",
        "bonuses:write",
        "bonuses:approve",
    ],
    ROLE_CUSTOMER_SERVICE: [
        "applications:read",
        "applications:write",
        "clients:read",
        "clients:write",
    ],
    ROLE_AUDITOR: ["*.read"],  # Read-only access to all resources
    ROLE_LOAN_MANAGEMENT_OFFICER: [
        "loan_applications:read",
        "loan_applications:write",
        "loan_applications:submit",
        "loan_applications:upload_documents",
        "branches:read",
        "clients:read",
        "clients:write",
    ],
    ROLE_LOAN_OFFICER: [
        "loan_applications:read",
        "loan_applications:review",
        "loan_applications:approve",
        "loan_applications:reject",
        "loan_applications:request_info",
        "loan_applications:view_documents",
        "loan_applications:add_notes",
        "branches:read",
        "clients:read",
    ],
}


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
        "metadata": payload.get("metadata", {}),
    }
    request.state.principal = {"username": user["username"], "roles": user["roles"], "metadata": user.get("metadata", {})}
    return user


def require_roles(*needed: str):
    needed_set = set(needed)

    async def _dep(user=Depends(get_current_user)):
        if not needed_set.intersection(set(user.get("roles", []))):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


def require_permission(permission: str):
    """
    Dependency to check if user has a specific permission

    Args:
        permission: Permission string (e.g., "bicycles:read", "applications:approve")

    Returns:
        User dict if authorized

    Raises:
        HTTPException: If user doesn't have permission
    """

    async def _dep(user=Depends(get_current_user)):
        user_roles = user.get("roles", [])

        # Admin always has access
        if ROLE_ADMIN in user_roles:
            return user

        # Collect all permissions from user's roles
        user_permissions: set[str] = set()
        for role in user_roles:
            role_perms = ROLE_PERMISSIONS.get(role, [])
            user_permissions.update(role_perms)

        # Check for exact permission match
        if permission in user_permissions:
            return user

        # Check for wildcard permissions
        # Example: "*.read" matches "bicycles:read", "applications:read", etc.
        permission_parts = permission.split(":")
        if len(permission_parts) == 2:
            resource, action = permission_parts

            # Check for "resource:*" wildcard
            if f"{resource}:*" in user_permissions:
                return user

            # Check for "*.action" wildcard
            if f"*.{action}" in user_permissions:
                return user

        # Check for full wildcard
        if "*" in user_permissions:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required",
        )

    return _dep


async def require_branch_access(branch_id: str, user: dict[str, Any], db: AsyncSession) -> bool:
    """
    Check if user has access to a specific branch

    Args:
        branch_id: ID of the branch to check access for
        user: User dict from get_current_user
        db: Database session

    Returns:
        True if user has access

    Raises:
        HTTPException: If user doesn't have access to the branch
    """
    user_roles = user.get("roles", [])

    # Admin always has access
    if ROLE_ADMIN in user_roles:
        return True

    # Branch managers only have access to their assigned branch
    if ROLE_BRANCH_MANAGER in user_roles:
        user_branch_id = user.get("metadata", {}).get("branch_id")
        if user_branch_id == branch_id:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You can only access branch {user_branch_id}",
        )

    # Other roles have access to all branches
    return True


