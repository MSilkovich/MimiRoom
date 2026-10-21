from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.exceptions import PermissionDeniedError, InvalidCredentialsError, UnauthorizedError


class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except UnauthorizedError as exc:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "message": str(exc.detail)}
            )

        except InvalidCredentialsError as exc:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "message": str(exc.detail)}
            )

        except PermissionDeniedError as exc:
            return JSONResponse(
                status_code=403,
                content={"error": "Access Denied", "message": str(exc.detail)}
            )

        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"error": "Unhandled Exception", "message": ""}
            )
