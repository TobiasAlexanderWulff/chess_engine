from __future__ import annotations

import logging
from typing import Any, Dict, cast

from fastapi import Request
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from starlette import status
from fastapi.exceptions import RequestValidationError


logger = logging.getLogger(__name__)


def error_envelope(
    *,
    code: str,
    message: str,
    err_type: str,
    request_id: str,
    field_errors: list[dict[str, str]] | None = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "type": err_type,
            "request_id": request_id,
        }
    }
    if field_errors:
        payload["error"]["field_errors"] = field_errors
    return payload


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    if isinstance(exc, FastAPIHTTPException):
        status_code = exc.status_code
        code = _status_to_code(status_code)
        payload = error_envelope(
            code=code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            err_type="client_error" if 400 <= status_code < 500 else "server_error",
            request_id=request_id,
        )
        return JSONResponse(status_code=status_code, content=payload)
    # Fallback (shouldn't happen with registration), treat as 500
    payload = error_envelope(
        code="internal_error",
        message="Internal Server Error",
        err_type="server_error",
        request_id=request_id,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    # If it's an HTTPException, render structured client/server error accordingly
    if isinstance(exc, FastAPIHTTPException):
        status_code = exc.status_code
        code = _status_to_code(status_code)
        payload = error_envelope(
            code=code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            err_type="client_error" if 400 <= status_code < 500 else "server_error",
            request_id=request_id,
        )
        return JSONResponse(status_code=status_code, content=payload)
    # Otherwise, treat as internal error and log it
    logger.exception("Unhandled exception", extra={"request_id": request_id})
    payload = error_envelope(
        code="internal_error",
        message="Internal Server Error",
        err_type="server_error",
        request_id=request_id,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


async def request_validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    # Map Pydantic/FastAPI validation errors to our structured envelope with 422
    errors = []
    rve = cast(RequestValidationError, exc)
    for e in rve.errors():
        loc = ".".join(str(p) for p in e.get("loc", []) if p is not None)
        msg = e.get("msg", "invalid value")
        typ = e.get("type", "value_error")
        errors.append({"field": loc, "code": typ, "message": msg})
    payload = error_envelope(
        code="unprocessable_entity",
        message="Validation error",
        err_type="client_error",
        request_id=request_id,
        field_errors=errors or None,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


def _status_to_code(status_code: int) -> str:
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not_found"
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "bad_request"
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if status_code == status.HTTP_409_CONFLICT:
        return "conflict"
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return "unprocessable_entity"
    if 500 <= status_code < 600:
        return "internal_error"
    return "error"
