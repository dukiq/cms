from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_ID = int(getenv("ADMIN_ID", 0))
DELETE_PASSWORD = getenv("DELETE_PASSWORD", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не указан в .env")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID не указан в .env")

if not DELETE_PASSWORD:
    raise ValueError("DELETE_PASSWORD не указан в .env")
