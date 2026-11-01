from dotenv import load_dotenv
import os

load_dotenv()

is_dev = os.getenv("DEV", "true") == "true"
port = int(os.getenv("PORT", 5000))
url: str = os.getenv("DATABASE_URL", "")
client_site = os.getenv("CLIENT_SITE", "localhost:3000")
host = os.getenv("HOST")