from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from .principal import Principal, PrincipalKind
from .auth import (
    auth_bearer_scheme,
    get_current_user,
    get_unverified_token_payload,
    is_access_token_payload,
)
from .service_auth import decode_service_token


async def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(
        auth_bearer_scheme),
) -> Principal:
    """Принципал запроса: пользователь (access-токен) или сервис (service-токен).

    Оба типа токена приходят в одном и том же заголовке
    ``Authorization: Bearer <token>`` — именно поэтому их нельзя различить
    отдельными security-схемами (оба читали бы один и тот же заголовок и
    «побеждал» бы один из них). Тип определяется по claims самого токена:

    - ``type == access`` и есть ``sub`` -> пользователь;
    - иначе -> пробуем сервисный токен (пустой payload или ``type == service``).

    Один эндпоинт, помеченный ``Depends(get_principal)``, обслуживает и
    клиентов, и сервисы.
    """
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = get_unverified_token_payload(token)

    if is_access_token_payload(payload):
        user = await get_current_user(credentials=credentials)
        return Principal(kind=PrincipalKind.USER, user=user)

    service_payload = decode_service_token(token)
    return Principal(kind=PrincipalKind.SERVICE, service_payload=service_payload)
