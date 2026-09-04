from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUserDep, UserServiceDep, get_current_user
from app.exceptions.user import UserAlreadyExistsError
from app.permissions import Permission, require_permission
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get('/me', response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUserDep,
):
    return current_user


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_permission(Permission.USER_READ))])
async def list_users(service: UserServiceDep, skip: int = 0, limit: int = 20):
    return await service.list(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)]
)
async def get_user(user_id: int, service: UserServiceDep):
    return await service.get_by_id(
        user_id
    )  # Exception is handled by app.exception_handler


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(data: UserCreate, service: UserServiceDep):
    try:
        return await service.create(data)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )


@router.patch('/me', response_model=UserResponse)
async def update_current_user(
        data: UserUpdate,
        current_user: CurrentUserDep,
        service: UserServiceDep
):
    return await service.update(current_user.id, data)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.USER_UPDATE))]
)
async def update_user(user_id: int, data: UserUpdate, service: UserServiceDep):
    return await service.update(
        user_id, data
    )  # Exception is handled by app.exception_handler


@router.delete(
    '/me',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_current_user(
        current_user: CurrentUserDep,
        service: UserServiceDep
):
    return await service.delete(current_user.id)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.USER_DELETE))],
)
async def delete_user(user_id: int, service: UserServiceDep):
    await service.delete(user_id)  # Exception is handled by app.exception_handler


@router.patch(
    "/{user_id}/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.USER_DISABLE))],
)
async def disable_user(user_id: int, service: UserServiceDep):
    return await service.disable(user_id)
