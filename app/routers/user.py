from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import UserServiceDep
from app.exceptions.user import UserAlreadyExistsError
from app.permissions import Permission, require_permission
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserServiceDep):
    return await service.get_by_id(
        user_id
    )  # Exception is handled by app.exception_handler


@router.post("", response_model=UserResponse)
async def create_user(data: UserCreate, service: UserServiceDep):
    try:
        return await service.create(data)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, service: UserServiceDep):
    return await service.update(
        user_id, data
    )  # Exception is handled by app.exception_handler


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.USER_DELETE))],
)
async def delete_user(user_id: int, service: UserServiceDep):
    await service.delete(user_id)  # Exception is handled by app.exception_handler
