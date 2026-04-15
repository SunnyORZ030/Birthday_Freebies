from app.db import get_connection_url
from app.services.starbucks_ingestion_service import run_starbucks_ingestion


if __name__ == "__main__":
    # CLI-friendly local PoC runner: crawl -> stage -> promote for bay_area.
    result = run_starbucks_ingestion(
        get_connection_url(),
        region_code="bay_area",
    )
    print(result)