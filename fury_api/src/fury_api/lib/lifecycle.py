"""
# Application State Management

The State object provides shared resources throughout the application lifecycle:

- logger: A pre-configured application logger that ensures consistent logging
  across all endpoints and services, eliminating the need to repeatedly configure
  loggers in different parts of the codebase.

# Accessing State in Request Handlers:

State resources are available via the FastAPI Request object during request handling.
Access them using `request.state.<resource_name>`:

Example:
    from fastapi import Request
    from fury_api.lib.logging import Logger

    @router.get("/example")
    async def my_endpoint(request: Request):
        logger: Logger = request.state.logger
        logger.info("Processing request")
        return {"status": "ok"}

Note: The lifespan context manager ensures state is initialized before any
request is processed and cleaned up when the application shuts down.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from fury_api.lib import logging
from fury_api.lib.settings import config

__all__ = ["lifespan", "on_startup", "on_shutdown"]


class State(TypedDict):
    logger: logging.Logger


@asynccontextmanager
async def lifespan(app: FastAPI | None = None) -> AsyncGenerator[State, None]:
    await on_startup()

    state = State(
        logger=logging.get_logger(config.app.SLUG),
    )
    yield state

    await on_shutdown()


async def on_startup() -> None:
    """Executed on application startup."""
    logging.configure()


async def on_shutdown() -> None:
    """Executed on application shutdown."""
    # TODO: Leaving this here just in case it's needed later
    pass
