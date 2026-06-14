from fastapi import FastAPI
from app.database import init_db
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.categories import router as categories_router
from app.routers.transactions import router as transactions_router
from app.routers.budgets import router as budgets_router
from app.routers.parser import router as parser_router

app = FastAPI(title="Personal Finance Manager")

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(parser_router)


@app.on_event("startup")
def on_startup():
    init_db()
