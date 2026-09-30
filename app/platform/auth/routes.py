from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Auth, DbSession
from app.core.config import get_settings
from app.schemas.auth import AuthMeResponse, LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse, OrganizationResponse
from app.services import auth as auth_service
from app.tenant.resolver import get_organization

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=AuthMeResponse, status_code=201)
async def register(data: RegisterRequest, db: DbSession):
    user, organization = await auth_service.register(db, data)
    return {"user": UserResponse.model_validate(user), "organization": OrganizationResponse.model_validate(organization)}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DbSession):
    access, refresh = await auth_service.login(db, data.login, data.password, data.organization_id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DbSession):
    access, refresh_token = await auth_service.refresh(db, data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=204)
async def logout(data: LogoutRequest, db: DbSession):
    await auth_service.logout(db, data.refresh_token)


@router.get("/me", response_model=AuthMeResponse)
async def me(auth: Auth, db: DbSession):
    from app.models import User
    user = await db.get(User, auth.user_id)
    organization = await get_organization(db, auth.tenant.organization_id)
    return {"user": user, "organization": organization}
