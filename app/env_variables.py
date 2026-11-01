from dotenv import load_dotenv
import os

load_dotenv()
url: str = os.getenv("DATABASE_URL", "")

treated_uri = ""

if url.startswith("postgres://"):
    treated_uri = url.replace("postgres://", "postgresql://", 1)
else:
    treated_uri = url

is_dev = os.getenv("DEV", "true") == "true"
port = int(os.getenv("PORT", 5000))
client_site = os.getenv("CLIENT_SITE", "localhost:3000")
host = os.getenv("HOST")
