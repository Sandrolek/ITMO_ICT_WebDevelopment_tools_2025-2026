from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from connection import init_db, get_session
from models import (
    User, UserCreate, UserRead,
    Account, AccountCreate, AccountUpdate, AccountRead,
    Category, CategoryCreate, CategoryRead,
    Transaction, TransactionCreate, TransactionRead,
)

app = FastAPI(title="Personal Finance Manager — Practice 2")


@app.on_event("startup")
def on_startup():
    init_db()


# --- Users ---

@app.post("/users", response_model=UserRead, status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    user = User.model_validate(data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# --- Accounts ---

@app.post("/accounts", response_model=AccountRead, status_code=201)
def create_account(data: AccountCreate, session: Session = Depends(get_session)):
    account = Account.model_validate(data)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@app.get("/accounts", response_model=list[AccountRead])
def get_accounts(session: Session = Depends(get_session)):
    return session.exec(select(Account)).all()


@app.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    return account


@app.patch("/accounts/{account_id}", response_model=AccountRead)
def update_account(account_id: int, data: AccountUpdate, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    session.delete(account)
    session.commit()
    return {"detail": "deleted"}


# --- Categories ---

@app.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(data: CategoryCreate, session: Session = Depends(get_session)):
    category = Category.model_validate(data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@app.get("/categories", response_model=list[CategoryRead])
def get_categories(session: Session = Depends(get_session)):
    return session.exec(select(Category)).all()


@app.get("/categories/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    session.delete(category)
    session.commit()
    return {"detail": "deleted"}


# --- Transactions ---

@app.post("/transactions", response_model=TransactionRead, status_code=201)
def create_transaction(data: TransactionCreate, session: Session = Depends(get_session)):
    category_ids = data.category_ids
    txn = Transaction(
        amount=data.amount,
        description=data.description,
        date=data.date,
        type=data.type,
        account_id=data.account_id,
    )
    for cat_id in category_ids:
        cat = session.get(Category, cat_id)
        if not cat:
            raise HTTPException(404, f"Category {cat_id} not found")
        txn.categories.append(cat)
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


@app.get("/transactions", response_model=list[TransactionRead])
def get_transactions(session: Session = Depends(get_session)):
    return session.exec(select(Transaction)).all()


@app.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, session: Session = Depends(get_session)):
    txn = session.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return txn


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, session: Session = Depends(get_session)):
    txn = session.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    session.delete(txn)
    session.commit()
    return {"detail": "deleted"}
