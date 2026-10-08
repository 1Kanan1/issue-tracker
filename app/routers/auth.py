from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import UserServiceDep
from app.exceptions.user import AuthenticationError
from app.rate_limit import (
    check_account_locked,
    clear_failures,
    rate_limit_login,
    register_failure,
)
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_login)]
)
async def login(
    data: LoginRequest,
    service: UserServiceDep,
):
    check_account_locked(data.username)

    try:
        user = await service.authenticate(data.username, data.password)
    except AuthenticationError:
        register_failure(data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_failures(data.username)

    return TokenResponse(access_token=create_access_token(user.id), token_type="bearer")
