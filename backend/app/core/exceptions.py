import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = error_response(message=str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": body["success"], "data": body["data"], "error": body["error"]},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        body = error_response(message="Validation error", details=exc.errors())
        return JSONResponse(
            status_code=422,
            content={"success": body["success"], "data": body["data"], "error": body["error"]},
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error_handler(_: Request, exc: OperationalError) -> JSONResponse:
        logger.exception("Database operational error", exc_info=exc)
        body = error_response(message="Database unavailable")
        return JSONResponse(
            status_code=503,
            content={"success": body["success"], "data": body["data"], "error": body["error"]},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error", exc_info=exc)
        body = error_response(message="Database request failed")
        return JSONResponse(
            status_code=503,
            content={"success": body["success"], "data": body["data"], "error": body["error"]},
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        body = error_response(message="Internal server error")
        return JSONResponse(
            status_code=500,
            content={"success": body["success"], "data": body["data"], "error": body["error"]},
        )
