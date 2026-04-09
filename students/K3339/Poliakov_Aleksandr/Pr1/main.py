from fastapi import FastAPI, HTTPException
from models import (
    Account, AccountCreate, AccountUpdate,
    Transaction, TransactionCreate,
    Category, CategoryCreate,
)

app = FastAPI(title="Personal Finance Manager — Practice 1")

# In-memory storage
accounts_db: dict[int, dict] = {}
transactions_db: dict[int, dict] = {}
categories_db: dict[int, dict] = {}

account_id_counter = 1
transaction_id_counter = 1
category_id_counter = 1


# --- Categories ---

@app.get("/categories", response_model=list[Category])
def get_categories():
    return list(categories_db.values())


@app.post("/categories", response_model=Category, status_code=201)
def create_category(data: CategoryCreate):
    global category_id_counter
    category = Category(id=category_id_counter, **data.model_dump())
    categories_db[category_id_counter] = category.model_dump()
    category_id_counter += 1
    return category


# --- Accounts ---

@app.get("/accounts", response_model=list[Account])
def get_accounts():
    result = []
    for acc in accounts_db.values():
        txns = [t for t in transactions_db.values() if t.get("account_id") == acc["id"]]
        enriched = [_enrich_transaction(t) for t in txns]
        result.append({**acc, "transactions": enriched})
    return result


@app.get("/accounts/{account_id}", response_model=Account)
def get_account(account_id: int):
    acc = accounts_db.get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    txns = [t for t in transactions_db.values() if t.get("account_id") == acc["id"]]
    enriched = [_enrich_transaction(t) for t in txns]
    return {**acc, "transactions": enriched}


@app.post("/accounts", response_model=Account, status_code=201)
def create_account(data: AccountCreate):
    global account_id_counter
    account = Account(id=account_id_counter, **data.model_dump())
    accounts_db[account_id_counter] = account.model_dump()
    account_id_counter += 1
    return account


@app.put("/accounts/{account_id}", response_model=Account)
def update_account(account_id: int, data: AccountUpdate):
    acc = accounts_db.get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    update = data.model_dump(exclude_unset=True)
    acc.update(update)
    accounts_db[account_id] = acc
    return acc


@app.delete("/accounts/{account_id}")
def delete_account(account_id: int):
    if account_id not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    del accounts_db[account_id]
    return {"detail": "deleted"}


# --- Transactions ---

@app.get("/transactions", response_model=list[Transaction])
def get_transactions():
    return [_enrich_transaction(t) for t in transactions_db.values()]


@app.post("/transactions", response_model=Transaction, status_code=201)
def create_transaction(data: TransactionCreate):
    global transaction_id_counter
    payload = data.model_dump()
    category_id = payload.pop("category_id", None)

    txn = {
        "id": transaction_id_counter,
        "amount": payload["amount"],
        "description": payload.get("description"),
        "date": payload["date"],
        "type": payload["type"],
        "category_id": category_id,
        "account_id": None,
    }
    transactions_db[transaction_id_counter] = txn
    transaction_id_counter += 1
    return _enrich_transaction(txn)


# --- Helpers ---

def _enrich_transaction(txn: dict) -> dict:
    category = None
    if txn.get("category_id") and txn["category_id"] in categories_db:
        category = categories_db[txn["category_id"]]
    return {
        "id": txn["id"],
        "amount": txn["amount"],
        "description": txn["description"],
        "date": txn["date"],
        "type": txn["type"],
        "category": category,
    }
