"""Fetch marine weather data from Open-Meteo Marine API.

Free, no API key required.
Docs: https://open-meteo.com/en/docs/marine-weather-api
"""

import json
from datetime import UTC, datetime

import httpx

from src.db.duck import dump_raw, get_connection

# Malaysian fishing spots -- lat, lon, name
FISHING_SPOTS = [
    {"lat": 5.5, "lon": 103.0, "name": "Kuala Terengganu"},  # East coast
    {"lat": 4.2, "lon": 103.4, "name": "Kerteh"},
    {"lat": 6.2, "lon": 102.2, "name": "Pantai Sabak (Kelantan)"},
    {"lat": 2.8, "lon": 104.1, "name": "Tioman"},
    {"lat": 5.3, "lon": 100.3, "name": "Penang (west)"},
]

# Variables we want from the API
MARINE_PARAMS = [
    "wave_height",
    "wave_direction",
    "wave_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "sea_surface_temperature",
    "ocean_current_velocity",
]


def build_url(lat: float, lon: float) -> str:
    """Build the Open-Meteo marine API URL for a location."""
    params_hourly = ",".join(MARINE_PARAMS)
    return (
        f"https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly={params_hourly}"
        f"&timezone=Asia%2FKuala_Lumpur"
        f"&forecast_days=3"
    )


def fetch_spot(lat: float, lon: float) -> dict | None:
    """Fetch marine data for a single lat/lon. Returns raw JSON."""
    url = build_url(lat, lon)
    print(f"  Fetching {url}")

    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("=" * 50)
    print("WTF — Marine Data Ingestion")
    print(f"  Started at: {datetime.now(UTC).isoformat()}")
    print("=" * 50)

    con = get_connection()

    for spot in FISHING_SPOTS:
        name = spot["name"]
        lat = spot["lat"]
        lon = spot["lon"]

        print(f"\n  #{name} ({lat}, {lon})")

        try:
            raw = fetch_spot(lat, lon)
            if raw is None:
                continue

            # Attach metadata
            raw["_spot_name"] = name
            raw["_ingested_at"] = datetime.now(UTC).isoformat()

            dump_raw(con, "marine_raw", [raw])

        except httpx.HTTPError as e:
            print(f"  [err] HTTP error: {e}")
        except Exception as e:
            print(f"  [err] Unexpected error: {e}")

    con.close()
    print("\nDone. Data is in bronze.marine_raw")


if __name__ == "__main__":
    main()
