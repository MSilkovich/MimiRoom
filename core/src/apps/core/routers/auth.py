from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import dependencies as deps
from src.schemas.auth import (
    RegisterRequest, TokenRequest, RefreshRequest, TokenResponse, LogoutRequest,
)
from src.models import TokenType
from src.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    user = await auth.register(payload)
    return await auth.issue_pair(user.user_id)


@router.post("/token", response_model=TokenResponse)
async def login(payload: TokenRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    if payload.grant_type != "password":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "grant_type must be password")
    user_id = await auth.authenticate(payload.username, payload.password)
    return await auth.issue_pair(user_id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    if payload.grant_type != TokenType.REFRESH:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "grant_type must be refresh")
    return await auth.refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
async def logout(payload: LogoutRequest, auth: AuthService = Depends(deps.get_service(AuthService))):
    await auth.logout(payload.refresh_token)
