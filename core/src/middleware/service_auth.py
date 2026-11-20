from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer

from config.jwt import settings_jwt

# Значение claim `type` для сервисных токенов. Пользовательские токены имеют
# type = access/refresh, поэтому это надёжный признак «свой/чужой», даже если
# секреты сервиса и пользователя случайно совпадают.
SERVICE_TOKEN_TYPE = "service"

service_bearer_scheme = HTTPBearer(
    auto_error=False, scheme_name="ServiceToken")


def decode_service_token(token: str) -> dict:
    """Проверить сервисный токен и вернуть его payload.

    Сервисные токены подписываются отдельным секретом
    (``SERVICE_JWT_SECRET``) и, как правило, не имеют срока жизни.

    Исторически сервисный токен может быть с пустым payload. Такие токены
    принимаем для обратной совместимости. Но если в токене явно указан
    ``type``, он обязан быть ``service`` — это не позволяет использовать
    пользовательский access/refresh токен как сервисный.
    """
    try:
        payload = jwt.decode(
            token,
            settings_jwt.SERVICE_JWT_SECRET,
            algorithms=[settings_jwt.SERVICE_JWT_ALG],
            options={"verify_exp": False},
        )
    except JWTError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            f"Invalid service token: {e}")

    token_type = payload.get("type")
    if token_type is not None and token_type != SERVICE_TOKEN_TYPE:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Not a service token")

    return payload
