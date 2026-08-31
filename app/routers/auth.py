from fastapi import APIRouter, HTTPException, status

from app.deps import UserServiceDep
from app.exceptions.user import AuthenticationError
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: UserServiceDep):
    try:
        user = await service.authenticate(data.username, data.password)
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id), token_type="bearer")
