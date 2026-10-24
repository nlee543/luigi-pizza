"""Single-origin launcher: original team API at /api, existing UI at /."""

from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.main import create_app
from integration import router, provision, IntegrationBase

ROOT = Path(__file__).resolve().parents[1]
api = create_app(
    cookie_secure=False,
    allowed_origin=os.getenv(
        "APP_ORIGIN",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://testserver",
    ),
)
api.include_router(router)


@asynccontextmanager
async def lifespan(app):
    async with api.router.lifespan_context(api):
        with api.state.sessions() as session:
            IntegrationBase.metadata.create_all(session.bind)
            provision(session)
        yield


app = FastAPI(lifespan=lifespan)


# Prevent legacy write routes from bypassing the extension's transaction rules.
# Original standalone api.main remains available to the team's own tests/tools.
@app.middleware("http")
async def integrated_write_contract(request, call_next):
    path = request.url.path
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and path.startswith("/api/")
        and not path.startswith(("/api/auth/", "/api/bridge/"))
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {
                "detail": "Use /api/bridge/command for integrated business changes; legacy writes are read-only in integrated mode."
            },
            status_code=409,
        )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


app.mount("/api", api)
for directory in ["js", "css", "assets"]:
    app.mount("/" + directory, StaticFiles(directory=ROOT / directory), name=directory)


@app.get("/")
def home():
    return FileResponse(ROOT / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/runtime.js")
def runtime():
    from fastapi.responses import Response

    return Response(
        "window.LUIGI_API = true;",
        media_type="text/javascript",
        headers={"Cache-Control": "no-store"},
    )
