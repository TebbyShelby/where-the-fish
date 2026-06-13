"""DuckDB connection & bronze layer helpers."""

from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEV_DB = DATA_DIR / "dev.duckdb"


def get_connection(db_path: Path = DEV_DB) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the given database file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def ensure_bronze_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create bronze schema if it doesn't exist."""
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")


def dump_raw(con: duckdb.DuckDBPyConnection, table: str, records: list[dict]) -> None:
    """Insert a list of dicts into bronze.<table>, creating the table if needed."""
    if not records:
        print(f"  [warn] No records to insert into bronze.{table}")
        return

    ensure_bronze_schema(con)

    # Create table from first record's keys
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS bronze.{table} (
            _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data JSON
        )
    """)

    # Insert each record as a JSON blob
    for rec in records:
        con.execute(
            f"INSERT INTO bronze.{table} (data) VALUES (?::JSON)",
            [rec],
        )

    print(f"  ✓ Inserted {len(records)} rows into bronze.{table}")
