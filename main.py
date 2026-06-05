import time
from contextlib import asynccontextmanager

from api.auth import router as auth_router
from core.secrets import secret_manager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db_pass = secret_manager.get_db_password()
        jwt_key = secret_manager.get_auth_secret_key()
        if not db_pass or not jwt_key:
            raise ValueError("Loaded secrets contain empty values")
    except Exception as e:
        raise RuntimeError("Startup failed - check Vault connectivity and secret paths") from e
    yield


app_config = {
    "title": "Test API",
    "openapi_url": "/api/openapi.json",
    "docs_url": "/openapi",
    "redoc_url": "/docs",
    "lifespan": lifespan,
}
app = FastAPI(**app_config)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    try:
        db_pass = secret_manager.get_db_password()
        jwt_key = secret_manager.get_auth_secret_key()
        redis_pass = secret_manager.get_redis_password()
        return {
            "status": "ok",
            "db_password_len": len(db_pass),
            "jwt_key_len": len(jwt_key),
            "redis_pass_len": len(redis_pass),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
