from fastapi import FastAPI
from app.database import init_db
from app.routers.auth import router as auth_router

app = FastAPI(title="Personal Finance Manager")

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    init_db()
