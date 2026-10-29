from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.settings import settings
from backend.app.database.connection import get_connection
from backend.app.routes.admin_routes import router as admin_router
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.directory_routes import router as directory_router
from backend.app.routes.service_routes import router as service_router
from backend.app.routes.cmdb_routes import router as cmdb_router
from backend.app.routes.desk_routes import router as desk_router
from backend.app.routes.process_routes import router as process_router
from backend.app.routes.experience_routes import router as experience_router

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(directory_router, prefix=settings.api_prefix)
app.include_router(service_router, prefix=settings.api_prefix)
app.include_router(cmdb_router, prefix=settings.api_prefix)
app.include_router(desk_router, prefix=settings.api_prefix)
app.include_router(process_router, prefix=settings.api_prefix)
app.include_router(experience_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
    except Exception as error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from error
    return {"status": "ok", "database": "ok"}
