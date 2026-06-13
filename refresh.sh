#!/bin/bash
# refresh.sh — Fetch latest data and rebuild fishing scores
# Run this whenever you want fresh fishing conditions.
#
# Usage: bash refresh.sh

set -e

echo "=== Where The Fish — Data Refresh ==="

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install/update dependencies
pip install -e ".[dashboard]" --quiet

# Ingest fresh data
echo ""
echo "[1/4] Fetching marine data (waves, swell, sea temp)..."
python -m src.ingest.marine

echo ""
echo "[2/4] Fetching weather forecast..."
python -m src.ingest.weather

echo ""
echo "[3/4] Fetching tide data..."
python -m src.ingest.tide || echo "  [warn] TideCheck may be rate-limited. Skipping."

# Rebuild dbt models
echo ""
echo "[4/4] Building dbt models..."
dbt build --profiles-dir dbt/profiles

echo ""
echo "=== Done ==="
echo "Run: streamlit run dashboard/app.py"
