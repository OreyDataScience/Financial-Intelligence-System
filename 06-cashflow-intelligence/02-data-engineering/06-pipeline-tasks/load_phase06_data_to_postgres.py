
"""
Orey Analytics
Phase 06 - Cashflow Intelligence
Processed CSV to PostgreSQL loader

Step 1: Locate and inspect the processed CSV inputs.
"""

import csv
import sys
import os
import psycopg
from pathlib import Path


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

PROCESSED_DIR = PROJECT_ROOT / "01-data" / "03-processed"


# ---------------------------------------------------------
# 2. CSV FILES AND DESTINATION TABLES
# ---------------------------------------------------------

CSV_TABLES = {
    "business_profiles_processed.csv": "business_profiles",
    "bank_transactions_processed.csv": "bank_transactions",
    "invoices_processed.csv": "invoices",
    "supplier_bills_processed.csv": "supplier_bills",
    "investigation-queue.csv": "investigation_queue",
    "duplicates-removed.csv": "duplicates_removed",
    "profile-conflicts.csv": "profile_conflicts",
    "data-quality-metrics.csv": "data_quality_metrics",
}


# ---------------------------------------------------------
# 3. INSPECT INPUT FILES
# ---------------------------------------------------------

def inspect_csv_files():
    """Check that every required CSV exists and is readable."""

    print("=" * 65)
    print("OREY ANALYTICS - PHASE 06 DATABASE LOADER")
    print("=" * 65)

    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Processed data: {PROCESSED_DIR}\n")

    if not PROCESSED_DIR.is_dir():
        raise FileNotFoundError(
            f"Processed data directory not found: {PROCESSED_DIR}"
        )

    total_rows = 0
    file_counts = {}

    for filename, table_name in CSV_TABLES.items():
        file_path = PROCESSED_DIR / filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Required CSV is missing: {file_path}"
            )

        with file_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:
            reader = csv.reader(csv_file)

            headers = next(reader, None)

            if not headers:
                raise ValueError(
                    f"The CSV is empty or has no header: {filename}"
                )

            if any(not header.strip() for header in headers):
                raise ValueError(
                    f"The CSV contains an empty column name: {filename}"
                )

            if len(headers) != len(set(headers)):
                raise ValueError(
                    f"The CSV contains duplicate column names: {filename}"
                )

            row_count = sum(1 for _ in reader)

        file_counts[table_name] = row_count
        total_rows += row_count

        print(
            f"OK  {filename:<38} "
            f"{row_count:>7,} rows"
        )

    print("-" * 65)
    print(f"Files checked: {len(file_counts)}")
    print(f"Total CSV records: {total_rows:,}")
    print("\nInput inspection completed successfully.")

    return file_counts

def test_database_connection():
    """Connect to PostgreSQL and verify the target database."""

    database_url = os.environ.get("OREY_DATABASE_URL")

    connection_settings = {
        "host": "localhost",
        "port": 5432,
        "dbname": "orey_cashflow_dev",
        "user": "postgres",
    }

    print("\nChecking PostgreSQL connection...")

    if database_url:
        connection = psycopg.connect(database_url, connect_timeout=10)
    else:
        connection = psycopg.connect(
            **connection_settings,
            password=os.environ.get("PGPASSWORD") or None,
            connect_timeout=10,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT current_database(), current_schema(),
                       version()
            """)
            database, schema, version = cursor.fetchone()

        if database != "orey_cashflow_dev":
            raise RuntimeError(
                f"Connected to unexpected database: {database}"
            )

        print(f"Connected database: {database}")
        print(f"Current schema: {schema}")
        print(f"PostgreSQL: {version.split(',')[0]}")
        print("Database connection successful.")

    finally:
        connection.close()

# ---------------------------------------------------------
# 4. ENTRY POINT
# ---------------------------------------------------------

def main():
    try:
        inspect_csv_files()
        test_database_connection()
    except (OSError, ValueError, psycopg.Error, RuntimeError) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
