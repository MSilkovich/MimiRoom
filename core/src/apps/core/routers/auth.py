from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import dependencies as deps
from src.schemas.auth import (
    RegisterRequest, TokenRequest, RefreshRequest, TokenResponse, LogoutRequest,
)
from src.models import TokenType
from src.services.auth_service import AuthService
from src.exceptions import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(uow_factory: deps.UowFactoryDep) -> AuthService:
    return AuthService(uow_factory)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    try:
        user = await auth.register(payload)
    except UserAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")
    return await auth.issue_pair(user.user_id)


@router.post("/token", response_model=TokenResponse)
async def login(payload: TokenRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    if payload.grant_type != "password":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "grant_type must be password")
    try:
        user_id = await auth.authenticate(payload.username, payload.password)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Invalid credentials")
    return await auth.issue_pair(user_id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    if payload.grant_type != TokenType.REFRESH:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "grant_type must be refresh")
    try:
        return await auth.refresh(payload.refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))


@router.post("/logout", status_code=204)
async def logout(payload: LogoutRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    await auth.logout(payload.refresh_token)
