from fastapi import FastAPI
from app.database import init_db

app = FastAPI(title="Personal Finance Manager")


@app.on_event("startup")
def on_startup():
    init_db()
