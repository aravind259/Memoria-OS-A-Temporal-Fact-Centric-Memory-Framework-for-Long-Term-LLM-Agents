from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.core.container import lifecycle_scheduler

app = FastAPI(
    title="Memory OS",
    version="1.0"
)

# Configure CORS for actual frontend development origins only (no wildcard)
cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(memory_router)


@app.on_event("startup")
def startup_event():
    print("[FastAPI] Server startup: Launching Background Memory Lifecycle Scheduler...")
    try:
        lifecycle_scheduler.start()
    except Exception as e:
        print(f"[FastAPI Warning] Could not start lifecycle scheduler: {e}")


@app.on_event("shutdown")
def shutdown_event():
    print("[FastAPI] Server shutdown: Stopping Background Memory Lifecycle Scheduler...")
    try:
        lifecycle_scheduler.stop()
    except Exception as e:
        print(f"[FastAPI Warning] Could not stop lifecycle scheduler: {e}")


# Resolve absolute root workspace directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(BASE_DIR, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Memory OS Backend Server Running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Memory OS"}