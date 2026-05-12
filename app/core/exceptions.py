from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SQLParseException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidDialectException(Exception):
    def __init__(self, dialect: str) -> None:
        self.dialect = dialect
        self.message = f"Dialect '{dialect}' is not supported."
        super().__init__(self.message)


async def sql_parse_exception_handler(request: Request, exc: SQLParseException) -> JSONResponse:
    logger.error("SQL parse error", extra={"endpoint": str(request.url.path), "message": exc.message})
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "SQL_PARSE_ERROR", "message": exc.message},
    )


async def invalid_dialect_exception_handler(request: Request, exc: InvalidDialectException) -> JSONResponse:
    logger.error("Invalid dialect", extra={"endpoint": str(request.url.path), "dialect": exc.dialect})
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": "INVALID_DIALECT", "message": exc.message},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."},
    )
