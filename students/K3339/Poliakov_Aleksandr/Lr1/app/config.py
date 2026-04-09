import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/finance_db")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
