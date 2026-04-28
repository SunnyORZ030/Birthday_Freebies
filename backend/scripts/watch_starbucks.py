from app.db import get_connection_url
from app.services.starbucks_watch_service import run_starbucks_watch_once_from_env


if __name__ == "__main__":
    result = run_starbucks_watch_once_from_env(get_connection_url())
    print(result)
