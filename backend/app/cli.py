"""
Backend CLI Utility.
Provides administrative operations including dataset importation, integrity
verification, and database health inspection.
"""

import argparse
import sys
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.database.base import Base
from app.database.session import engine
from app.services.ingestion import IngestionService, calculate_sha256


def _resolve_dataset_path(file_arg: str) -> Path:
    file_path = Path(file_arg)
    if file_path.is_absolute() or file_path.exists():
        return file_path

    # Check relative to the repository root (backend/app/cli.py -> root).
    root_candidate = Path(__file__).resolve().parent.parent.parent / file_arg
    return root_candidate if root_candidate.exists() else file_path


def _ensure_schema() -> None:
    if settings.is_production:
        logger.warning(
            "Production mode: relying on Alembic migrations. Run "
            "'alembic upgrade head' before importing data."
        )
        return
    Base.metadata.create_all(bind=engine)


def import_dataset_command(args: argparse.Namespace) -> None:
    """Execute dataset ingestion from CSV."""
    file_path = _resolve_dataset_path(args.file)
    if not file_path.is_file():
        print(f"[!] Dataset file not found: {file_path.resolve()}", file=sys.stderr)
        sys.exit(1)

    checksum = calculate_sha256(file_path)
    print(f"[*] Dataset checksum (SHA-256): {checksum}")
    if args.expected_checksum and checksum != args.expected_checksum:
        print("[!] Checksum mismatch against --expected-checksum.", file=sys.stderr)
        sys.exit(1)

    _ensure_schema()

    print(f"[*] Database dialect: {engine.dialect.name}")
    print(f"[*] Ingesting dataset from: {file_path.resolve()}")
    try:
        summary = IngestionService.import_csv(
            csv_path=file_path,
            dataset_id=args.id,
            force=args.force,
            chunk_size=args.chunk_size,
            strict=args.strict,
        )
        print("\n=== DATASET INGESTION SUMMARY ===")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print("=================================\n")
    except Exception as e:  # noqa: BLE001 - CLI boundary
        print(f"[!] Ingestion failed (transaction rolled back): {e}", file=sys.stderr)
        sys.exit(1)


def verify_dataset_command(args: argparse.Namespace) -> None:
    """Verify database counts, checksums, and ground-truth integrity."""
    _ensure_schema()
    result = IngestionService.verify_database(strict=args.strict)
    print("\n=== DATASET VERIFICATION ===")
    for key, value in result.items():
        print(f"  {key}: {value}")

    if args.expected_checksum:
        latest_checksum = result["latest_import"]["checksum_sha256"]
        checksum_ok = latest_checksum == args.expected_checksum
        print(f"  checksum_matches: {checksum_ok}")
    else:
        checksum_ok = True

    integrity_ok = result["orphan_ground_truth_rows"] == 0 and (
        not args.strict or result["transactions_without_ground_truth"] == 0
    )
    print("============================\n")
    if not (checksum_ok and integrity_ok):
        sys.exit(1)


def health_command(_: argparse.Namespace) -> None:
    """Print database health information."""
    from app.database.session import check_db_health

    health = check_db_health()
    print("\n=== DATABASE HEALTH ===")
    for key, value in health.items():
        print(f"  {key}: {value}")
    print("=======================\n")
    if not health["connected"]:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Sentinel.AML Backend CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser(
        "import-dataset", help="Bulk import synthetic transactions CSV"
    )
    import_parser.add_argument(
        "--file", "-f", default="data/transactions.csv", help="Path to CSV file"
    )
    import_parser.add_argument(
        "--id", default="synthetic-promptwars-2026", help="Dataset identifier"
    )
    import_parser.add_argument(
        "--force", action="store_true", help="Force re-import (clears existing data)"
    )
    import_parser.add_argument(
        "--chunk-size", type=int, default=IngestionService.CHUNK_SIZE, help="Rows per batch"
    )
    import_parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail when transactions lack ground-truth rows",
    )
    import_parser.add_argument(
        "--expected-checksum",
        default=None,
        help="Optional expected SHA-256 of the CSV file",
    )
    import_parser.set_defaults(func=import_dataset_command)

    verify_parser = subparsers.add_parser(
        "verify-dataset", help="Verify row counts and ground-truth integrity"
    )
    verify_parser.add_argument("--strict", action="store_true", help="Require labels for every row")
    verify_parser.add_argument(
        "--expected-checksum",
        default=None,
        help="Optional expected SHA-256 of the latest import",
    )
    verify_parser.set_defaults(func=verify_dataset_command)

    health_parser = subparsers.add_parser("db-health", help="Check database connectivity")
    health_parser.set_defaults(func=health_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
