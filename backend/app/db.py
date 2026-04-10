import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

# Load backend/.env so DATABASE_URL is available in local development.
load_dotenv()


def _normalized_database_url(raw_url: str) -> str:
    # Prisma URLs can include ?schema=public; psycopg does not need this value.
    parsed = urlparse(raw_url)
    query_params = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "schema"
    ]
    return urlunparse(parsed._replace(query=urlencode(query_params)))


def get_connection_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to start the FastAPI server.")
    return _normalized_database_url(database_url)