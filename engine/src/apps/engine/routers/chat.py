"""
Путь: /chat*
- POST    /                          — принять сообщение на обработку
"""

from fastapi import APIRouter, Depends, Security


router = APIRouter(prefix="/users", tags=["users"], dependencies=[
    # Depends(get_current_user),
])


@router.post("", response_model=any)
async def proccess(
    # limit: int = 100, offset: int = 0, service: Service = Depends(deps.get_service(UserService))
):
    """Принять сообщение на обработку"""
    return None
