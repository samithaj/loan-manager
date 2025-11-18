from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from .middleware import correlation_id_middleware, request_logging_middleware
from .errors import install_error_handlers
from .config import get_settings
from .routers import users as users_router
from .routers import reference as reference_router
from .routers import clients as clients_router
from .db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
from .services.users import verify_credentials
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets  # noqa: F401
from .routers import loan_products as loan_products_router
from .routers import loans as loans_router
from .routers import charges as charges_router
from .routers import collateral as collateral_router
from .routers import documents as documents_router
from .routers import jobs as jobs_router
from .routers import delinquency as delinquency_router
from .routers import reschedule as reschedule_router
from .routers import reports as reports_router
from .routers import webhooks as webhooks_router
from .routers import public_bicycles as public_bicycles_router
from .routers import bicycle_applications as bicycle_applications_router
from .routers import bicycles as bicycles_router
from .routers import hr_leave as hr_leave_router
from .routers import hr_attendance as hr_attendance_router
from .routers import hr_bonus as hr_bonus_router
from .routers import workshop_parts as workshop_parts_router
from .routers import workshop_jobs as workshop_jobs_router
from .routers import companies as companies_router
from .routers import bike_lifecycle as bike_lifecycle_router
from .routers import bike_transfers as bike_transfers_router
from .routers import bike_sales as bike_sales_router
from .routers import bike_expenses as bike_expenses_router
from .routers import bike_reports as bike_reports_router
from .routers import admin as admin_router
from loguru import logger
from .auth import router as auth_router
from .rbac import get_current_user
from fastapi.staticfiles import StaticFiles
from pathlib import Path


security = HTTPBasic()


class User(BaseModel):
    username: str
    roles: list[str]


async def verify_basic_auth(request: Request, credentials: HTTPBasicCredentials = Depends(security)) -> User:
    settings = get_settings()
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid credentials"},
            headers={"WWW-Authenticate": "Basic"},
        )
    if settings.demo_open_basic_auth:
        user = User(username=credentials.username, roles=["user"])
        request.state.principal = {"username": user.username, "roles": user.roles}
        return user
    async with SessionLocal() as session:  # type: AsyncSession
        user = await verify_credentials(session, credentials.username, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "UNAUTHORIZED", "message": "Invalid credentials"},
                headers={"WWW-Authenticate": "Basic"},
            )
        request.state.principal = {"username": user.username, "roles": user.roles}
        return User(username=user.username, roles=user.roles)


def create_app() -> FastAPI:
    app = FastAPI(title="Loan Manager API", version="0.1.0")
    # Configure structured JSON logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), serialize=True, backtrace=False, diagnose=False)
    app.middleware("http")(correlation_id_middleware)
    app.middleware("http")(request_logging_middleware)
    install_error_handlers(app)
    # Dev CORS for Next.js on localhost:3000, localhost:3010, and localhost:3020
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3010",
            "http://127.0.0.1:3010",
            "http://localhost:3020",
            "http://127.0.0.1:3020"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    api = APIRouter(prefix="/v1")

    @api.get("/health")
    def health(request: Request) -> dict[str, str]:
        logger.bind(route="/health", correlationId=getattr(request.state, "correlation_id", None)).info("healthcheck")
        return {"status": "ok"}

    @api.get("/me", response_model=User)
    def me(request: Request, user_dict: dict = Depends(get_current_user)) -> User:
        user = User(username=user_dict.get("username"), roles=user_dict.get("roles", []))
        logger.bind(route="/me", username=user.username, roles=user.roles, correlationId=getattr(request.state, "correlation_id", None)).info("me")
        return user

    app.include_router(api)
    app.include_router(users_router.router)
    app.include_router(reference_router.router)
    app.include_router(clients_router.router)
    app.include_router(loan_products_router.router)
    app.include_router(loans_router.router)
    app.include_router(charges_router.router)
    app.include_router(collateral_router.router)
    app.include_router(documents_router.router)
    app.include_router(jobs_router.router)
    app.include_router(delinquency_router.router)
    app.include_router(reschedule_router.router)
    app.include_router(reports_router.router)
    app.include_router(webhooks_router.router)
    app.include_router(public_bicycles_router.router)
    app.include_router(bicycle_applications_router.router)
    app.include_router(bicycles_router.router)
    app.include_router(hr_leave_router.router)
    app.include_router(hr_attendance_router.router)
    app.include_router(hr_bonus_router.router)
    app.include_router(workshop_parts_router.router)
    app.include_router(workshop_jobs_router.router)
    app.include_router(companies_router.router)
    app.include_router(bike_lifecycle_router.router)
    app.include_router(bike_transfers_router.router)
    app.include_router(bike_sales_router.router)
    app.include_router(bike_expenses_router.router)
    app.include_router(bike_reports_router.router)
    app.include_router(admin_router.router)
    app.include_router(auth_router)

    # Mount static files for uploaded images
    uploads_path = Path("uploads")
    uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    return app


app = create_app()


