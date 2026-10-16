#!/usr/bin/env python3
"""Audit an existing JP ZIP without rebuilding or bypassing build checks."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_release import MAX_ASSET, audit_output_text, load_charset, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--font-charset", type=Path, required=True)
    parser.add_argument("--all-candidates", action="store_true",
                        help="Include every Latin/kana candidate's file and JSON Pointer")
    args = parser.parse_args()
    require(args.zip.stat().st_size <= MAX_ASSET, "ZIP too large")
    data = args.zip.read_bytes()
    report = audit_output_text(data, load_charset(args.font_charset), args.all_candidates)
    report["zip_sha256"] = hashlib.sha256(data).hexdigest()
    report["charset_sha256"] = hashlib.sha256(args.font_charset.read_bytes()).hexdigest()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
