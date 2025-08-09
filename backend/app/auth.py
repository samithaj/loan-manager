from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from jose import jwt, JWTError
from loguru import logger
from pydantic import BaseModel

from .config import get_settings
from .services.users import verify_credentials
from .db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


router = APIRouter(prefix="/v1", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


def _load_or_generate_keys() -> tuple[bytes, bytes, str]:
    settings = get_settings()
    priv = getattr(settings, "jwt_private_key_pem", None)
    pub = getattr(settings, "jwt_public_key_pem", None)
    if priv and pub:
        private_pem = priv.encode("utf-8")
        public_pem = pub.encode("utf-8")
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    kid = sha1(public_pem).hexdigest()[:16]
    return private_pem, public_pem, kid


PRIVATE_PEM, PUBLIC_PEM, KID = _load_or_generate_keys()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sign_access(user: Any) -> str:
    settings = get_settings()
    exp = _now() + timedelta(minutes=getattr(settings, "jwt_access_ttl_minutes", 15))
    payload: dict[str, Any] = {
        "iss": getattr(settings, "jwt_issuer", "http://localhost:8000/auth"),
        "aud": getattr(settings, "jwt_audience", "loan-manager"),
        "sub": user.username,
        "roles": getattr(user, "roles", []),
        "jti": str(uuid4()),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
        "uname": user.username,
    }
    headers = {"kid": KID}
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256", headers=headers)


def _sign_refresh(user: Any) -> str:
    settings = get_settings()
    exp = _now() + timedelta(days=getattr(settings, "jwt_refresh_ttl_days", 7))
    payload: dict[str, Any] = {
        "iss": getattr(settings, "jwt_issuer", "http://localhost:8000/auth"),
        "aud": getattr(settings, "jwt_audience", "loan-manager"),
        "sub": user.username,
        "typ": "refresh",
        "jti": str(uuid4()),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    headers = {"kid": KID}
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256", headers=headers)


@router.post("/auth/login")
async def login(resp: Response, body: LoginBody, request: Request):
    async with SessionLocal() as session:  # type: AsyncSession
        user = await verify_credentials(session, body.username, body.password)
        if not user:
            logger.bind(route="/auth/login", username=body.username).warning("login failed")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    access = _sign_access(user)
    refresh = _sign_refresh(user)
    # Cookies: HttpOnly; Secure in non-debug; SameSite=Lax
    settings = get_settings()
    secure_flag = False  # dev only: allow cookies on http://localhost
    resp.set_cookie(
        "access_token",
        access,
        httponly=True,
        secure=secure_flag,
        samesite="lax",
        path="/",
        max_age=getattr(settings, "jwt_access_ttl_minutes", 15) * 60,
    )
    resp.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=secure_flag,
        samesite="lax",
        path="/",
        max_age=getattr(settings, "jwt_refresh_ttl_days", 7) * 24 * 3600,
    )
    logger.bind(route="/auth/login", username=body.username).info("login success")
    return {"ok": True}


@router.post("/auth/logout")
async def logout(resp: Response):
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@router.get("/.well-known/jwks.json")
async def jwks():
    # Minimal JWKS for RS256
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric import rsa as rsa_mod
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    # Build components from PUBLIC_PEM
    pub = serialization.load_pem_public_key(PUBLIC_PEM)
    if not isinstance(pub, rsa_mod.RSAPublicKey):
        raise HTTPException(500, "Invalid public key")
    numbers = pub.public_numbers()
    # base64url without padding
    import base64

    def b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    n = b64u(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big"))
    e = b64u(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big"))
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": KID,
                "use": "sig",
                "alg": "RS256",
                "n": n,
                "e": e,
            }
        ]
    }


