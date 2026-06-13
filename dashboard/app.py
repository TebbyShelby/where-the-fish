"""Streamlit dashboard for Where The Fish — fishing intelligence."""

import os
import sys
from pathlib import Path

import duckdb
import streamlit as st

# Path to DuckDB database
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "dev.duckdb"


def get_db():
    """Return a DuckDB connection."""
    return duckdb.connect(str(DB_PATH))


def load_scores(db, location_filter=None, days=3):
    """Load fishing scores from DuckDB."""
    where = "1=1"
    if location_filter:
        where = f"location = '{location_filter}'"

    query = f"""
        SELECT
            location,
            forecast_date,
            avg_wave_height,
            avg_sea_temp,
            min_temp_celsius,
            max_temp_celsius,
            summary_forecast,
            high_tide_count,
            wave_score,
            temp_score,
            weather_score,
            tide_score,
            air_temp_bonus,
            overall_score,
            fishing_rating
        FROM silver.fishing_score
        WHERE forecast_date >= current_date - 1
          AND forecast_date <= current_date + 2
          AND {where}
        ORDER BY forecast_date, overall_score DESC
        LIMIT 50
    """
    return db.execute(query).fetchdf()


def load_locations(db):
    """Get distinct locations from fishing_score."""
    return [
        row[0]
        for row in db.execute("""
            SELECT DISTINCT location
            FROM silver.fishing_score
            ORDER BY location
        """).fetchall()
    ]


def rating_color(rating):
    """Return hex color for a fishing rating."""
    colors = {
        "Excellent": "#22c55e",
        "Good": "#16a34a",
        "Fair": "#eab308",
        "Poor": "#ef4444",
    }
    return colors.get(rating, "#6b7280")


def main():
    st.set_page_config(
        page_title="Where The Fish",
        page_icon="fishing",
        layout="wide",
    )

    st.title("Where The Fish")
    st.caption("Should you go fishing today?")

    db = get_db()

    # Verify DB has data
    try:
        score_count = db.execute(
            "SELECT count(*) FROM silver.fishing_score"
        ).fetchone()[0]
        if score_count == 0:
            st.warning(
                "No data found. Run the ingestion pipeline first: "
                "`python -m src.ingest.marine` and `python -m src.ingest.weather`"
            )
            return
    except Exception:
        st.error("Database not initialized. Run dbt first: `dbt run`")
        return

    # Sidebar filters
    locations = load_locations(db)
    selected_location = st.sidebar.selectbox(
        "Location",
        ["All locations"] + locations,
    )

    location_filter = None
    if selected_location != "All locations":
        location_filter = selected_location

    scores = load_scores(db, location_filter)
    if scores.empty:
        st.info("No scores available for the selected filters.")
        return

    # Top-level metrics
    today = scores[scores["forecast_date"] == scores["forecast_date"].max()]
    if not today.empty:
        best = today.loc[today["overall_score"].idxmax()]
        avg = today["overall_score"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Best spot today",
            best["location"],
            f"{best['overall_score']}/100",
        )
        col2.metric(
            "Average score",
            f"{avg:.0f}/100",
        )
        col3.metric(
            "Locations scored",
            len(today),
        )

    st.divider()

    # Score breakdown chart
    st.subheader("Score Breakdown by Location")

    chart_data = scores.copy()
    chart_data["date_label"] = chart_data["forecast_date"].astype(str)

    st.bar_chart(
        chart_data,
        x="location",
        y=["wave_score", "temp_score", "weather_score", "tide_score", "air_temp_bonus"],
        stack=True,
        color=["#3b82f6", "#ef4444", "#eab308", "#22c55e", "#a78bfa"],
    )

    # Detailed table
    st.subheader("Details")

    display = scores.rename(columns={
        "location": "Location",
        "forecast_date": "Date",
        "avg_wave_height": "Wave (m)",
        "avg_sea_temp": "Sea Temp (C)",
        "min_temp_celsius": "Min (C)",
        "max_temp_celsius": "Max (C)",
        "summary_forecast": "Weather",
        "overall_score": "Score",
        "fishing_rating": "Rating",
    })

    display["Rating"] = display["Rating"].apply(
        lambda r: f'{rating_color(r)} {r}'
    )

    st.dataframe(
        display[
            [
                "Location", "Date", "Wave (m)", "Sea Temp (C)",
                "Min (C)", "Max (C)", "Weather", "Score", "Rating",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.caption(
        "Data sources: Open-Meteo (waves) | data.gov.my (weather) "
        "| TideCheck (tides) | dbt transforms | DuckDB"
    )


if __name__ == "__main__":
    main()
