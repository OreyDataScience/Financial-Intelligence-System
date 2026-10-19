
"""
Orey Analytics
Phase 06 - Cash Flow Intelligence
Transactional processed-data loader for PostgreSQL.

- Validates CSV inputs and database columns before modifying data.
- Loads all eight tables in one transaction.
- Checks row counts and reconciliation relationships.
- Rolls back the complete load if any step fails.
"""

import csv
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql


# =========================================================
# 1. PROJECT CONFIGURATION
# =========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "01-data" / "03-processed"

SCHEMA = "processed"

# Parent tables and bank transactions must load before their
# dependent ledger and audit records.
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

CONNECTION_SETTINGS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "orey_cashflow_dev",
    "user": "postgres",
    "connect_timeout": 10,
}


# =========================================================
# 2. INSPECT CSV FILES
# =========================================================

def inspect_csv_files():
    """Check required CSVs, headers, and record counts."""

    print("=" * 68)
    print("OREY ANALYTICS - PHASE 06 DATABASE LOADER")
    print("=" * 68)
    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Processed data: {PROCESSED_DIR}\n")

    if not PROCESSED_DIR.is_dir():
        raise FileNotFoundError(
            f"Processed data directory not found: {PROCESSED_DIR}"
        )

    results = {}

    for filename, table in CSV_TABLES.items():
        path = PROCESSED_DIR / filename

        if not path.is_file():
            raise FileNotFoundError(f"Missing required CSV: {path}")

        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.reader(file)
            headers = next(reader, None)

            if not headers or any(not h.strip() for h in headers):
                raise ValueError(
                    f"Missing or empty column names in {filename}"
                )

            if len(headers) != len(set(headers)):
                raise ValueError(
                    f"Duplicate column names in {filename}"
                )

            row_count = 0
            for row in reader:
                row_count += 1

                if len(row) != len(headers):
                    raise ValueError(
                        f"Malformed CSV row {row_count + 1} "
                        f"in {filename}: expected {len(headers)} "
                        f"fields, got {len(row)}"
                    )

        results[table] = {
            "path": path,
            "headers": headers,
            "row_count": row_count,
        }

        print(f"OK  {filename:<38} {row_count:>7,} rows")

    total = sum(item["row_count"] for item in results.values())

    print("-" * 68)
    print(f"Files checked: {len(results)}")
    print(f"Total CSV records: {total:,}")
    print("Input inspection completed successfully.")

    return results


# =========================================================
# 3. DATABASE CONNECTION
# =========================================================

def connect_to_database():
    """Connect using environment variables, not hardcoded passwords."""

    database_url = os.environ.get("OREY_DATABASE_URL")

    if database_url:
        return psycopg.connect(
            database_url,
            connect_timeout=10,
        )

    return psycopg.connect(
        **CONNECTION_SETTINGS,
        password=os.environ.get("PGPASSWORD") or None,
    )


# =========================================================
# 4. VALIDATE CSV HEADERS AGAINST POSTGRESQL
# =========================================================

def prepare_column_mappings(connection, files):
    """
    Confirm destination tables exist and CSV columns are valid.

    Database-generated columns are excluded from inserts.
    Required non-generated columns must be supplied or have
    a database default.
    """

    mappings = {}

    with connection.cursor() as cursor:
        for filename, table in CSV_TABLES.items():
            cursor.execute(
                """
                SELECT
                    column_name,
                    is_nullable,
                    column_default,
                    is_generated,
                    is_identity,
                    identity_generation
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                ORDER BY ordinal_position
                """,
                (SCHEMA, table),
            )

            rows = cursor.fetchall()

            if not rows:
                raise RuntimeError(
                    f"Destination table {SCHEMA}.{table} "
                    "does not exist or has no visible columns."
                )

            metadata = {row[0]: row[1:] for row in rows}
            csv_headers = files[table]["headers"]

            unknown = set(csv_headers) - set(metadata)

            if unknown:
                raise ValueError(
                    f"{filename} contains columns absent from "
                    f"{SCHEMA}.{table}: {sorted(unknown)}"
                )

            # PostgreSQL computes generated columns itself.
            insertable_headers = [
                header
                for header in csv_headers
                if metadata[header][2] != "ALWAYS"
            ]

            missing_required = []

            for column, details in metadata.items():
                (
                    nullable,
                    default,
                    generated,
                    identity,
                    identity_generation,
                ) = details

                if column in insertable_headers:
                    continue

                generated_by_database = (
                    generated == "ALWAYS"
                    or (
                        identity == "YES"
                        and identity_generation == "ALWAYS"
                    )
                )

                if (
                    nullable == "NO"
                    and default is None
                    and not generated_by_database
                ):
                    missing_required.append(column)

            if missing_required:
                raise ValueError(
                    f"{filename} is missing required database "
                    f"columns for {SCHEMA}.{table}: "
                    f"{sorted(missing_required)}"
                )

            mappings[table] = insertable_headers

            ignored = set(csv_headers) - set(insertable_headers)

            print(f"\nValidated: {SCHEMA}.{table}")
            print(f"  CSV columns to load: {len(insertable_headers)}")

            if ignored:
                print(
                    "  Database-generated columns skipped: "
                    + ", ".join(sorted(ignored))
                )

    return mappings


# =========================================================
# 5. REPLACE DATA INSIDE ONE TRANSACTION
# =========================================================

def load_all_tables(connection, files, mappings):
    """Atomically replace all eight tables from processed CSVs."""

    table_identifiers = sql.SQL(", ").join(
        sql.Identifier(SCHEMA, table)
        for table in CSV_TABLES.values()
    )

    with connection.cursor() as cursor:
        print("\nClearing existing Phase 06 table contents...")
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {}").format(table_identifiers)
        )

    loaded_counts = {}

    for filename, table in CSV_TABLES.items():
        path = files[table]["path"]
        columns = mappings[table]

        copy_statement = sql.SQL(
            "COPY {} ({}) FROM STDIN"
        ).format(
            sql.Identifier(SCHEMA, table),
            sql.SQL(", ").join(
                sql.Identifier(column) for column in columns
            ),
        )

        print(f"\nLoading {SCHEMA}.{table}...")

        loaded = 0

        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            with connection.cursor() as cursor:
                with cursor.copy(copy_statement) as copy:
                    for row in reader:
                        # Match standard CSV import behaviour:
                        # empty, unquoted fields represent SQL NULL.
                        values = tuple(
                            None if row[column] == "" else row[column]
                            for column in columns
                        )

                        copy.write_row(values)
                        loaded += 1

        expected = files[table]["row_count"]

        if loaded != expected:
            raise RuntimeError(
                f"CSV row-count mismatch for {table}: "
                f"expected {expected}, loaded {loaded}"
            )

        loaded_counts[table] = loaded
        print(f"  Loaded {loaded:,} rows.")

    return loaded_counts


# =========================================================
# 6. VALIDATE LOADED DATA
# =========================================================

def validate_database(connection, files):
    """Verify counts and bank-to-ledger relationships."""

    print("\nRunning post-load validation...")

    with connection.cursor() as cursor:
        # Compare actual counts with the source CSV counts.
        for table in CSV_TABLES.values():
            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(
                    sql.Identifier(SCHEMA, table)
                )
            )

            actual = cursor.fetchone()[0]
            expected = files[table]["row_count"]

            if actual != expected:
                raise RuntimeError(
                    f"Validation failed for {table}: "
                    f"expected {expected}, found {actual}"
                )

            print(f"  PASS  {table}: {actual:,} rows")

        # Every bank-to-ledger link must be reciprocal.
        cursor.execute("""
            SELECT COUNT(*)
            FROM processed.bank_transactions AS b
            WHERE b.matched_ledger_type IS NOT NULL
              AND (
                (
                  b.matched_ledger_type = 'invoice'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM processed.invoices AS i
                    WHERE i.source_record_id =
                          b.matched_ledger_source_record_id
                      AND i.matched_bank_source_record_id =
                          b.source_record_id
                  )
                )
                OR
                (
                  b.matched_ledger_type = 'supplier_bill'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM processed.supplier_bills AS s
                    WHERE s.source_record_id =
                          b.matched_ledger_source_record_id
                      AND s.matched_bank_source_record_id =
                          b.source_record_id
                  )
                )
              )
        """)

        inconsistent_links = cursor.fetchone()[0]

        if inconsistent_links:
            raise RuntimeError(
                f"Found {inconsistent_links} non-reciprocal "
                "bank-to-ledger links."
            )

        print("  PASS  Bank-to-ledger links are reciprocal.")

        # One bank transaction must not be linked to both
        # an invoice and a supplier bill.
        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT matched_bank_source_record_id
                FROM processed.invoices
                WHERE matched_bank_source_record_id IS NOT NULL

                UNION ALL

                SELECT matched_bank_source_record_id
                FROM processed.supplier_bills
                WHERE matched_bank_source_record_id IS NOT NULL
            ) AS linked
            GROUP BY matched_bank_source_record_id
            HAVING COUNT(*) > 1
        """)

        duplicate_link_groups = cursor.fetchall()

        if duplicate_link_groups:
            raise RuntimeError(
                "A bank transaction is linked to multiple "
                "invoice/supplier-bill records."
            )

        print("  PASS  No bank transactions are shared across ledgers.")


# =========================================================
# 7. MAIN ENTRY POINT
# =========================================================

def main():
    connection = None

    try:
        files = inspect_csv_files()

        print("\nConnecting to PostgreSQL...")

        connection = connect_to_database()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), version()"
            )
            database, version = cursor.fetchone()

        if database != "orey_cashflow_dev":
            raise RuntimeError(
                f"Unexpected database '{database}'. "
                "Expected 'orey_cashflow_dev'."
            )

        print(f"Connected database: {database}")
        print(f"Server: {version.split(',')[0]}")

        # Check every mapping before truncating any table.
        mappings = prepare_column_mappings(connection, files)

        print("\nStarting transactional replacement...")

        # psycopg commits when this block exits successfully.
        # Any exception inside causes the transaction to roll back.
        with connection.transaction():
            load_all_tables(connection, files, mappings)
            validate_database(connection, files)

        print("\n" + "=" * 68)
        print("DATABASE LOAD COMMITTED SUCCESSFULLY")
        print("=" * 68)
        print("All eight tables loaded and validated.")
        print("Total source records:", sum(
            item["row_count"] for item in files.values()
        ))

    except (OSError, ValueError, RuntimeError, psycopg.Error) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        print(
            "The load did not complete successfully. "
            "If the transaction had started, its changes were rolled back.",
            file=sys.stderr,
        )
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
