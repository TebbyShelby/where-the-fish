"""Fetch weather forecast data from data.gov.my.

Malaysia's official open data portal. Free, no API key required.
Docs: https://developer.data.gov.my/realtime-api/weather
"""

from datetime import UTC, datetime

import httpx

from src.db.duck import dump_raw, get_connection

API_URL = "https://api.data.gov.my/weather/forecast/"


def fetch_all_forecast() -> list[dict]:
    """Fetch the complete weather forecast dataset (all locations, 7 days)."""
    print(f"  Fetching {API_URL}")
    resp = httpx.get(API_URL, timeout=30, follow_redirects=True)
    resp.raise_for_status()

    data = resp.json()
    print(f"  Received {len(data)} forecast records")
    return data


def main() -> None:
    print("=" * 50)
    print("WTF — Weather Forecast Ingestion")
    print(f"  Started at: {datetime.now(UTC).isoformat()}")
    print("=" * 50)

    con = get_connection()

    try:
        records = fetch_all_forecast()

        # Attach ingestion metadata
        for rec in records:
            rec["_ingested_at"] = datetime.now(UTC).isoformat()

        dump_raw(con, "weather_raw", records)

    except httpx.HTTPError as e:
        print(f"  [err] HTTP error: {e}")
    except Exception as e:
        print(f"  [err] Unexpected error: {e}")
    else:
        # Quick summary of unique locations
        location_ids = {r["location"]["location_id"] for r in records}
        location_names = {r["location"]["location_name"] for r in records}

        # Find coastal locations we care about
        coastal_keywords = [
            "Kuala Terengganu", "Kemaman", "Bachok", "Kota Bharu",
            "Rompin", "Pekan", "Mersing", "George Town",
        ]
        found_coastal = [
            name for name in location_names
            if any(k.lower() in name.lower() for k in coastal_keywords)
        ]

        print(f"\n  Summary:")
        print(f"     Total locations: {len(location_ids)}")
        print(f"     Total records:   {len(records)}")
        print(f"     Forecast days:   7")
        print(f"     Coastal spots:   {', '.join(sorted(found_coastal))}")

    con.close()
    print("\nDone. Data is in bronze.weather_raw")


if __name__ == "__main__":
    main()
