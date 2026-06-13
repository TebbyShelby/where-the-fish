"""Fetch tide predictions and solunar data from TideCheck API.

Free tier: 50 requests/day.
Sign up at https://tidecheck.com/developers

Station IDs can be found by:
  1. Go to https://tidecheck.com and search for your fishing spot
  2. The station ID is shown at the top of the tide chart page
     (e.g., for San Francisco the API path is /api/station/9414290/tides)
"""

import os
from datetime import UTC, datetime

import httpx
from dotenv import load_dotenv

from src.db.duck import dump_raw, get_connection

load_dotenv()

BASE_URL = "https://tidecheck.com/api/station"
API_KEY = os.getenv("TIDECHECK_API_KEY")

# Known Malaysian tide stations.
# To add more: search on tidecheck.com and grab the numeric station ID.
TIDE_STATIONS = {
    "Klang":        "klang-140a-mys-uhslc_rq",
    "Port Dickson": "fes2022-port-dickson",
}


def fetch_station_tides(station_id: str, days: int = 3) -> dict | None:
    """Fetch tide extremes and daily conditions for a station."""
    url = f"{BASE_URL}/{station_id}/tides?days={days}"
    print(f"  Fetching {url}")

    resp = httpx.get(url, headers={"X-API-Key": API_KEY}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    if not API_KEY:
        print("[err] TIDECHECK_API_KEY not set. Add it to .env file.")
        print("       Get a free key at https://tidecheck.com/developers")
        return

    if not TIDE_STATIONS:
        print("[warn] No tide stations configured.")
        print("       Add station IDs to the TIDE_STATIONS dict in tide.py")
        print("       Find station IDs at https://tidecheck.com")
        return

    print("=" * 50)
    print("WTF — Tide & Solunar Ingestion")
    print(f"  Started at: {datetime.now(UTC).isoformat()}")
    print("=" * 50)

    con = get_connection()

    for name, station_id in TIDE_STATIONS.items():
        print(f"\n  #{name} (station {station_id})")

        try:
            data = fetch_station_tides(station_id)
            if data is None:
                continue

            data["_spot_name"] = name
            data["_ingested_at"] = datetime.now(UTC).isoformat()

            dump_raw(con, "tide_raw", [data])

        except httpx.HTTPError as e:
            print(f"  [err] HTTP error: {e}")
        except Exception as e:
            print(f"  [err] Unexpected error: {e}")

    con.close()
    print("\nDone. Data is in bronze.tide_raw")


if __name__ == "__main__":
    main()
