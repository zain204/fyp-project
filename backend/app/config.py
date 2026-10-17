import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing in .env")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing in .env")