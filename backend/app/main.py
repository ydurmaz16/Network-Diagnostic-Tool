"""FastAPI application entry point."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.errors import DiagnosticError

logger = logging.getLogger("netdiag")

app = FastAPI(
    title="Network Diagnostic Tool",
    description="Small diagnostic API: ping, DNS, traceroute and single-port checks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _friendly_validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid request."
    first = errors[0]
    if "port" in first.get("loc", ()):
        return "Port must be a number between 1 and 65535."
    if first.get("type") == "value_error":
        return str(first["ctx"]["error"])
    return "Invalid request. Please check your input."


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": _friendly_validation_message(exc)})


@app.exception_handler(DiagnosticError)
async def diagnostic_handler(_: Request, exc: DiagnosticError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unexpected_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected error", exc_info=exc)  # details stay in the server log
    return JSONResponse(
        status_code=500, content={"detail": "Something went wrong on the server. Please try again."}
    )


app.include_router(router)

# Optional: serve the built frontend (frontend/dist) from the same process.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
