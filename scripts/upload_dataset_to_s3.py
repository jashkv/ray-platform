#!/usr/bin/env python3
# ==============================================================================
# File: scripts/upload_dataset_to_s3.py
# Role: S3 Dataset Ingestion and Pre-flight Validation CLI Utility
# Description: Validates and uploads corporate datasets (CSV feeds) to the Amazon S3
#              raw data landing zone (incoming/) for ingestion by the Ray distributed
#              pipeline and Iceberg lakehouse. Supports single-file, multi-file, and
#              directory batch uploads with pre-flight schema inspection, row count
#              verification (>= 1,000 records), SSE-KMS / SSE-S3 encryption,
#              object tagging/metadata, and dry-run execution.
# Inputs:      CSV files from local filesystem (default: application/data/*.csv).
# Outputs:     S3 objects under s3://<bucket>/<prefix><filename>.csv with metadata.
# Key Features:
#   - Zero-trust credential resolution (IAM role, IRSA, AWS profile, env vars)
#   - Pre-upload validation: readable CSV, non-empty, line count checking (>= 1,000 rows)
#   - Dynamic header auto-discovery summary
#   - SSE-KMS and SSE-S3 server-side encryption
#   - Offline dry-run mode for local development and CI/CD validation without AWS credentials
#   - Formatted output with ready-to-run ray_pipeline.py invocation arguments
# ==============================================================================
"""
S3 Dataset Ingestion & Validation CLI Utility.
Uploads corporate CSV datasets to Amazon S3 landing zone with pre-flight validation.
"""

import os
import sys
import csv
import hashlib
import argparse
import datetime
import subprocess
from typing import List, Dict, Any, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from application.src.ingest import auto_detect_columns
except ImportError:
    # Graceful fallback if invoked outside package context
    def auto_detect_columns(fieldnames: List[str]) -> Dict[str, str]:
        return {f: f for f in fieldnames}

# ANSI terminal colors
BOLD = "\033[1m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
RESET = "\033[0m"


def compute_file_md5(file_path: str) -> str:
    """Compute hex MD5 digest of a local file in 64KB chunks."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def format_bytes(size: int) -> str:
    """Convert bytes to human-readable size string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def validate_csv_dataset(
    file_path: str,
    min_rows: int = 1000,
    allow_small: bool = False
) -> Dict[str, Any]:
    """
    Perform pre-flight integrity inspection on a corporate CSV dataset.
    Validates file existence, non-emptiness, row count, and schema headers.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Dataset file does not exist: {file_path}")

    size_bytes = os.path.getsize(file_path)
    if size_bytes == 0:
        raise ValueError(f"Dataset file is empty (0 bytes): {file_path}")

    md5_checksum = compute_file_md5(file_path)

    # Inspect CSV structure
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(4096)
        f.seek(0)

        # Detect delimiter
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.reader(f, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"CSV file contains no header row: {file_path}")

        fieldnames = [c.strip() for c in header if c.strip()]
        if not fieldnames:
            raise ValueError(f"No valid column headers found in CSV: {file_path}")

        # Count data rows
        row_count = sum(1 for row in reader if any(field.strip() for field in row))

    # Evaluate row count requirement
    if row_count < min_rows and not allow_small:
        raise ValueError(
            f"Dataset '{os.path.basename(file_path)}' has {row_count} rows, which fails the "
            f"production requirement of at least {min_rows} records. Use --allow-small to bypass."
        )

    # Auto-detect semantic concepts
    mapped_concepts = auto_detect_columns(fieldnames)

    return {
        "path": os.path.abspath(file_path),
        "filename": os.path.basename(file_path),
        "size_bytes": size_bytes,
        "size_human": format_bytes(size_bytes),
        "md5": md5_checksum,
        "rows": row_count,
        "columns": fieldnames,
        "delimiter": delimiter,
        "detected_concepts": mapped_concepts,
        "meets_row_threshold": row_count >= min_rows,
    }


def resolve_s3_bucket(explicit_bucket: Optional[str], dry_run: bool = False) -> str:
    """
    Dynamically resolve target S3 bucket from CLI flags, environment variables,
    or Terraform state output.
    """
    if explicit_bucket and explicit_bucket.strip():
        return explicit_bucket.strip()

    # Check environment variables
    env_bucket = os.environ.get("DATA_BUCKET_NAME") or os.environ.get("DATA_BUCKET")
    if env_bucket and env_bucket.strip():
        return env_bucket.strip()

    # Fast-path fallback for dry-run mode
    if dry_run:
        return "dryrun-ray-platform-data-bucket"

    # Attempt to query Terraform data layer output
    tf_data_dir = os.path.join(REPO_ROOT, "terraform", "data")
    if os.path.isdir(tf_data_dir):
        try:
            res = subprocess.run(
                ["terraform", f"-chdir={tf_data_dir}", "output", "-raw", "s3_data_bucket_id"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip() and "No value" not in res.stdout:
                return res.stdout.strip()
        except Exception:
            pass

    # Attempt AWS CLI STS lookup to format convention
    try:
        sts_res = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if sts_res.returncode == 0 and sts_res.stdout.strip().isdigit():
            account_id = sts_res.stdout.strip()
            return f"test-ray-platform-data-{account_id}"
    except Exception:
        pass

    raise ValueError(
        "Could not determine target S3 bucket. Please specify --bucket <name> or "
        "set the DATA_BUCKET environment variable."
    )


class ProgressCallback:
    """Console progress callback for boto3 file upload."""

    def __init__(self, filename: str, total_bytes: int):
        self._filename = filename
        self._total_bytes = total_bytes
        self._seen_bytes = 0

    def __call__(self, bytes_transferred: int):
        self._seen_bytes += bytes_transferred
        pct = (self._seen_bytes / self._total_bytes * 100.0) if self._total_bytes > 0 else 100.0
        sys.stdout.write(
            f"\r{CYAN}[UPLOADING]{RESET} {self._filename}: "
            f"{format_bytes(self._seen_bytes)} / {format_bytes(self._total_bytes)} ({pct:.1f}%)"
        )
        sys.stdout.flush()
        if self._seen_bytes >= self._total_bytes:
            sys.stdout.write("\n")


def upload_dataset_to_s3(
    file_meta: Dict[str, Any],
    bucket: str,
    prefix: str = "incoming/",
    sse_algorithm: str = "aws:kms",
    kms_key_id: Optional[str] = None,
    dry_run: bool = False,
    s3_client: Optional[Any] = None,
) -> str:
    """
    Upload a validated dataset to S3 raw landing zone with encryption and metadata.
    Returns the final s3:// URI.
    """
    # Normalize prefix (strip leading slashes, guarantee single trailing slash)
    clean_prefix = prefix.strip("/")
    s3_key = f"{clean_prefix}/{file_meta['filename']}" if clean_prefix else file_meta["filename"]
    s3_uri = f"s3://{bucket}/{s3_key}"

    if dry_run:
        return s3_uri

    import boto3
    from botocore.exceptions import ClientError, BotoCoreError

    if s3_client is None:
        s3_client = boto3.client("s3")

    extra_args: Dict[str, Any] = {
        "ContentType": "text/csv",
        "Metadata": {
            "uploaded-by": "ray-platform-s3-uploader",
            "row-count": str(file_meta["rows"]),
            "md5-checksum": file_meta["md5"],
            "upload-timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "detected-columns": str(len(file_meta["columns"])),
        },
        "Tagging": "Environment=production&Project=ray-platform&Dataset=corporate_feed",
    }

    # Configure Zero-Trust Server-Side Encryption
    if sse_algorithm.lower() == "aws:kms":
        extra_args["ServerSideEncryption"] = "aws:kms"
        if kms_key_id:
            extra_args["SSEKMSKeyId"] = kms_key_id
    elif sse_algorithm.lower() in ["aes256", "s3"]:
        extra_args["ServerSideEncryption"] = "AES256"

    progress = ProgressCallback(file_meta["filename"], file_meta["size_bytes"])

    try:
        s3_client.upload_file(
            file_meta["path"],
            bucket,
            s3_key,
            ExtraArgs=extra_args,
            Callback=progress,
        )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Failed uploading {file_meta['filename']} to {s3_uri}: {e}")

    return s3_uri


def collect_target_files(
    file_args: Optional[List[str]],
    dir_arg: Optional[str]
) -> List[str]:
    """Collect unique local CSV file paths from arguments."""
    target_files: List[str] = []

    if file_args:
        for f in file_args:
            # Handle comma-separated list
            for sub_f in f.split(","):
                clean = sub_f.strip()
                if clean:
                    target_files.append(clean)

    if dir_arg:
        if not os.path.isdir(dir_arg):
            raise NotADirectoryError(f"Directory not found: {dir_arg}")
        for entry in sorted(os.listdir(dir_arg)):
            if entry.lower().endswith(".csv"):
                target_files.append(os.path.join(dir_arg, entry))

    # Default to application/data if nothing specified
    if not target_files:
        default_dir = os.path.join(REPO_ROOT, "application", "data")
        if os.path.isdir(default_dir):
            for entry in sorted(os.listdir(default_dir)):
                if entry.lower().endswith(".csv"):
                    target_files.append(os.path.join(default_dir, entry))

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for f in target_files:
        abs_p = os.path.abspath(f)
        if abs_p not in seen:
            seen.add(abs_p)
            deduped.append(f)

    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Insert and upload corporate datasets into Amazon S3 for Ray ingestion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload default datasets (application/data/*.csv) to S3
  python scripts/upload_dataset_to_s3.py --bucket my-corp-data-bucket

  # Dry-run validation (checks row counts, MD5, and headers without AWS calls)
  python scripts/upload_dataset_to_s3.py --dry-run

  # Upload a single arbitrary unforeseen CSV feed
  python scripts/upload_dataset_to_s3.py --file path/to/partner_feed.csv --bucket my-corp-data-bucket

  # Upload multiple files with custom KMS key
  python scripts/upload_dataset_to_s3.py -f feed1.csv,feed2.csv --kms-key-id alias/corporate-key
        """,
    )
    parser.add_argument(
        "-f", "--file",
        dest="files",
        action="append",
        help="Path to CSV dataset file (can be specified multiple times or comma-separated)",
    )
    parser.add_argument(
        "-d", "--dir",
        dest="dir",
        default=None,
        help="Directory containing CSV files to upload (default: application/data)",
    )
    parser.add_argument(
        "-b", "--bucket",
        dest="bucket",
        default=None,
        help="Destination Amazon S3 bucket name (falls back to DATA_BUCKET env var)",
    )
    parser.add_argument(
        "-p", "--prefix",
        dest="prefix",
        default="incoming/",
        help="S3 key prefix landing zone (default: 'incoming/')",
    )
    parser.add_argument(
        "--min-rows",
        dest="min_rows",
        type=int,
        default=1000,
        help="Minimum required row count per dataset (default: 1000)",
    )
    parser.add_argument(
        "--allow-small",
        dest="allow_small",
        action="store_true",
        help="Allow uploading datasets with fewer than --min-rows records",
    )
    parser.add_argument(
        "--sse",
        dest="sse",
        choices=["aws:kms", "AES256", "none"],
        default="aws:kms",
        help="Server-side encryption standard (default: aws:kms)",
    )
    parser.add_argument(
        "--kms-key-id",
        dest="kms_key_id",
        default=None,
        help="KMS Key ID or ARN for SSE-KMS encryption",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Perform pre-flight validation and output S3 URIs without making AWS API calls",
    )
    parser.add_argument(
        "-q", "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress per-file schema details",
    )
    parser.add_argument(
        "--trigger-pipeline",
        dest="trigger_pipeline",
        action="store_true",
        help="Emit event signal to automatically trigger Ray distributed pipeline upon upload",
    )

    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}==================================================================={RESET}")
    print(f"{BOLD}{CYAN}  Ray AI Platform — S3 Dataset Ingestion & Validation Utility{RESET}")
    print(f"{BOLD}{CYAN}==================================================================={RESET}\n")

    # 1. Collect target files
    try:
        target_files = collect_target_files(args.files, args.dir)
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Failed collecting target files: {e}", file=sys.stderr)
        return 1

    if not target_files:
        print(f"{YELLOW}[WARN]{RESET} No CSV files found to upload.", file=sys.stderr)
        return 1

    print(f"{BLUE}[INFO]{RESET} Discovered {BOLD}{len(target_files)}{RESET} candidate dataset(s) for ingestion.")

    # 2. Resolve S3 Bucket
    try:
        bucket = resolve_s3_bucket(args.bucket, dry_run=args.dry_run)
    except ValueError as e:
        print(f"{RED}[ERROR]{RESET} {e}", file=sys.stderr)
        return 1

    print(f"{BLUE}[INFO]{RESET} Destination S3 Bucket: {BOLD}{bucket}{RESET}")
    print(f"{BLUE}[INFO]{RESET} S3 Landing Zone Prefix: {BOLD}{args.prefix.strip('/')}/{RESET}")
    print(f"{BLUE}[INFO]{RESET} Mode: {BOLD}{YELLOW}DRY-RUN (Pre-flight validation only){RESET}" if args.dry_run else f"{BLUE}[INFO]{RESET} Mode: {BOLD}{GREEN}LIVE S3 UPLOAD{RESET}")
    print(f"{BLUE}[INFO]{RESET} Encryption: {BOLD}{args.sse}{RESET}" + (f" (KMS Key: {args.kms_key_id})" if args.kms_key_id else ""))
    print(f"{BLUE}[INFO]{RESET} Minimum Row Threshold: {BOLD}{args.min_rows}{RESET} records\n")

    # 3. Pre-flight Validation
    validated_files: List[Dict[str, Any]] = []
    print(f"{BOLD}--- [1/2] Pre-flight Dataset Integrity Verification ---{RESET}")
    for idx, fpath in enumerate(target_files, 1):
        try:
            meta = validate_csv_dataset(
                fpath,
                min_rows=args.min_rows,
                allow_small=args.allow_small,
            )
            validated_files.append(meta)
            status_tag = f"{GREEN}PASS (>= {args.min_rows}){RESET}" if meta["meets_row_threshold"] else f"{YELLOW}WARN (< {args.min_rows}){RESET}"
            print(f"  [{idx}/{len(target_files)}] {BOLD}{meta['filename']}{RESET}")
            print(f"      Rows:       {BOLD}{meta['rows']:,}{RESET} records [{status_tag}]")
            print(f"      Size:       {meta['size_human']} ({meta['size_bytes']:,} bytes)")
            print(f"      MD5:        {meta['md5']}")
            print(f"      Columns:    {len(meta['columns'])} detected")
            if not args.quiet:
                detected_str = ", ".join(f"{k} -> {v}" for k, v in meta["detected_concepts"].items())
                print(f"      Concepts:   {detected_str}")
            print("")
        except Exception as e:
            print(f"  [{idx}/{len(target_files)}] {RED}[FAILED]{RESET} {fpath}: {e}", file=sys.stderr)
            return 1

    # 4. Upload Execution
    print(f"{BOLD}--- [2/2] Ingestion / Upload Execution ---{RESET}")
    uploaded_uris: List[Tuple[str, str, int]] = []

    s3_client = None
    if not args.dry_run:
        try:
            import boto3
            s3_client = boto3.client("s3")
        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Failed initializing AWS S3 client: {e}", file=sys.stderr)
            print(f"{YELLOW}[HINT]{RESET} Ensure AWS credentials are configured via AWS_PROFILE, IAM Role, or IRSA.", file=sys.stderr)
            return 1

    for meta in validated_files:
        try:
            dest_uri = upload_dataset_to_s3(
                file_meta=meta,
                bucket=bucket,
                prefix=args.prefix,
                sse_algorithm=args.sse,
                kms_key_id=args.kms_key_id,
                dry_run=args.dry_run,
                s3_client=s3_client,
            )
            uploaded_uris.append((meta["filename"], dest_uri, meta["rows"]))
            if args.dry_run:
                print(f"  {CYAN}[DRY-RUN READY]{RESET} {meta['filename']} -> {BOLD}{dest_uri}{RESET}")
            else:
                print(f"  {GREEN}[UPLOADED]{RESET} {meta['filename']} -> {BOLD}{dest_uri}{RESET}")
        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Upload failed for {meta['filename']}: {e}", file=sys.stderr)
            return 1

    # 5. Formatted Summary and Pipeline Invocation Helper
    print(f"\n{BOLD}{GREEN}==================================================================={RESET}")
    print(f"{BOLD}{GREEN}  Dataset Ingestion Completed Successfully!{RESET}")
    print(f"{BOLD}{GREEN}==================================================================={RESET}\n")

    print(f"{BOLD}Summary of Datasets in S3 Landing Zone:{RESET}")
    for fname, uri, rows in uploaded_uris:
        print(f"  - {BOLD}{fname:<30}{RESET} {rows:>6,} records -> {CYAN}{uri}{RESET}")

    # Generate ready-to-use pipeline execution snippet
    s1_uri = next((u for f, u, _ in uploaded_uris if "s1" in f.lower() or "supply" in f.lower()), uploaded_uris[0][1])
    s2_uri = next((u for f, u, _ in uploaded_uris if "s2" in f.lower() or "financial" in f.lower()), uploaded_uris[-1][1] if len(uploaded_uris) > 1 else uploaded_uris[0][1])

    print(f"\n{BOLD}Distributed Ray Pipeline Invocation Example:{RESET}")
    print(f"  {YELLOW}python application/src/ray_pipeline.py \\{RESET}")
    print(f"    {YELLOW}--s1-input {s1_uri} \\{RESET}")
    print(f"    {YELLOW}--s2-input {s2_uri} \\{RESET}")
    print(f"    {YELLOW}--catalog-type glue \\{RESET}")
    print(f"    {YELLOW}--warehouse-path s3://{bucket}/iceberg-warehouse \\{RESET}")
    print(f"    {YELLOW}--output-model-dir application/models{RESET}\n")

    # 6. Event-Driven Signal Dispatch (if --trigger-pipeline requested)
    if args.trigger_pipeline:
        print(f"{BOLD}{CYAN}--- [3/3] Emitting Event Signal to Trigger Ray Pipeline ---{RESET}")
        primary_file = validated_files[0]
        dispatched = False

        # Attempt A: HTTP webhook signal to running API console
        try:
            import urllib.request
            req_data = json.dumps({
                "s1_path": primary_file["path"],
                "filename": primary_file["filename"]
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:8000/api/trigger-pipeline",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                print(f"  {GREEN}[SIGNAL DELIVERED]{RESET} Event signal delivered to Web Console: {resp_json.get('message')}")
                print(f"  {CYAN}[JOB ID]{RESET} {resp_json.get('job_id')} is now processing in background.")
                dispatched = True
        except Exception:
            pass

        # Attempt B: Direct standalone execution fallback if API not running
        if not dispatched:
            print(f"  {YELLOW}[SIGNAL BROADCAST]{RESET} Local API service not listening on :8000. Initiating direct Ray pipeline...")
            try:
                from application.src.ray_pipeline import run_pipeline
                s2_fallback = os.path.join(REPO_ROOT, "application", "data", "financial_data_s2.csv")
                if not os.path.isfile(s2_fallback):
                    s2_fallback = primary_file["path"]
                run_pipeline(
                    s1_path=primary_file["path"],
                    s2_path=s2_fallback,
                    output_dir=os.path.join(REPO_ROOT, "application", "models"),
                    iceberg_catalog_type="sqlite",
                    warehouse_path="/tmp/e2e_iceberg_warehouse"
                )
                print(f"  {GREEN}[PIPELINE COMPLETE]{RESET} Dataset ingested, Iceberg committed, and revenue model retrained successfully!")
            except Exception as e:
                print(f"  {RED}[ERROR]{RESET} Direct pipeline execution failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
