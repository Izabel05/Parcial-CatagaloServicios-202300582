from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.settings import settings
from backend.app.database.connection import get_connection
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.service_routes import router as service_router

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(service_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
    except Exception as error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from error
    return {"status": "ok", "database": "ok"}
