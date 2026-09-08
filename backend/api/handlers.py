import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import EntityNotFoundError, EntityInUseError

logger = logging.getLogger(__name__)


async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"{exc.entity_name} with ID {exc.entity_id} not found."})


async def entity_in_use_handler(request: Request, exc: EntityInUseError) -> JSONResponse:
    message = str(exc) if str(exc) else "This entity cannot be deleted because it is currently in use."
    return JSONResponse(status_code=409, content={"detail": message})


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred. Please try again later."}
    )


def register_exception_handlers(app: FastAPI):
    """Registers all exception handlers to the FastAPI app."""
    app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)  # type: ignore
    app.add_exception_handler(EntityInUseError, entity_in_use_handler)  # type: ignore
    app.add_exception_handler(Exception, global_exception_handler)
