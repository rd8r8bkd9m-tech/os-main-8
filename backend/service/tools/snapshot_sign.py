#!/usr/bin/env python3
"""CLI tool for snapshot operations.

Usage:
    python snapshot_sign.py <snapshot.json> <secret> --output signed.json
    python snapshot_verify.py <snapshot.json> <secret>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add backend path to sys.path so we can import service modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.service.tools.snapshot import (
    sign_snapshot,
    verify_snapshot,
    snapshot_to_json,
    snapshot_from_json,
)


def main_sign() -> None:
    """Sign a snapshot."""
    parser = argparse.ArgumentParser(description="Sign a knowledge snapshot")
    parser.add_argument("snapshot", help="Path to snapshot JSON file")
    parser.add_argument("secret", help="HMAC secret for signing")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"Error: {snapshot_path} not found", file=sys.stderr)
        sys.exit(1)

    try:
        snapshot_json = snapshot_path.read_text(encoding="utf-8")
        snapshot = snapshot_from_json(snapshot_json)
    except Exception as e:
        print(f"Error reading snapshot: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        signed = sign_snapshot(snapshot, args.secret)
        output = snapshot_to_json(signed)
    except Exception as e:
        print(f"Error signing snapshot: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Signed snapshot written to {args.output}")
    else:
        print(output)


def main_verify() -> None:
    """Verify a snapshot signature."""
    parser = argparse.ArgumentParser(description="Verify a knowledge snapshot signature")
    parser.add_argument("snapshot", help="Path to snapshot JSON file")
    parser.add_argument("secret", help="HMAC secret for verification")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"Error: {snapshot_path} not found", file=sys.stderr)
        sys.exit(1)

    try:
        snapshot_json = snapshot_path.read_text(encoding="utf-8")
        snapshot = snapshot_from_json(snapshot_json)
    except Exception as e:
        print(f"Error reading snapshot: {e}", file=sys.stderr)
        sys.exit(1)

    if verify_snapshot(snapshot, args.secret):
        print("✓ Signature valid")
        sys.exit(0)
    else:
        print("✗ Signature invalid or missing")
        sys.exit(1)


if __name__ == "__main__":
    import os

    script_name = os.path.basename(sys.argv[0])
    if "sign" in script_name:
        main_sign()
    elif "verify" in script_name:
        main_verify()
    else:
        print("Error: Use snapshot_sign.py or snapshot_verify.py", file=sys.stderr)
        sys.exit(1)

