"""
Backend CLI Utility.
Provides administrative operations including dataset importation and health inspection.
"""

import argparse
import sys
from pathlib import Path

from app.database.base import Base
from app.database.session import engine
from app.services.ingestion import IngestionService
from app.core.logging import logger


def import_dataset_command(args: argparse.Namespace) -> None:
    """Execute dataset ingestion from CSV."""
    file_path = Path(args.file)
    if not file_path.is_absolute():
        # Check relative to cwd and project root
        if not file_path.exists():
            root_candidate = Path(__file__).resolve().parent.parent.parent / args.file
            if root_candidate.exists():
                file_path = root_candidate

    print(f"[*] Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    print(f"[*] Ingesting dataset from: {file_path.resolve()}")
    try:
        summary = IngestionService.import_csv(
            csv_path=file_path,
            dataset_id=args.id,
            force=args.force,
        )
        print("\n=== DATASET INGESTION SUMMARY ===")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        print("=================================\n")
    except Exception as e:
        print(f"[!] Ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Sentinel.AML Backend CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # import-dataset subcommand
    import_parser = subparsers.add_parser("import-dataset", help="Bulk import synthetic transactions CSV")
    import_parser.add_argument("--file", "-f", default="data/transactions.csv", help="Path to CSV file")
    import_parser.add_argument("--id", default="synthetic-promptwars-2026", help="Dataset identifier")
    import_parser.add_argument("--force", action="store_true", help="Force re-import (clears existing data)")
    import_parser.set_defaults(func=import_dataset_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

