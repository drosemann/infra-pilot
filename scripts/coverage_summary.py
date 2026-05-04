#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path

def read_coverage(px_path: Path) -> float:
    # Fallback: try to parse coverage.xml if present
    if not px_path.exists():
        return 0.0
    import xml.etree.ElementTree as ET
    tree = ET.parse(px_path)
    root = tree.getroot()
    line_rate = root.attrib.get("line-rate")
    try:
        return float(line_rate) * 100.0
    except Exception:
        return 0.0

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Print current coverage percentage from coverage.xml if available.")
    parser.add_argument("path", nargs="?", default("coverage.xml"), help="Path to coverage.xml")
    args = parser.parse_args()
    cov = read_coverage(Path(args.path))
    print(f"Current coverage: {cov:.2f}%")
    # Also print JSON for automation
    print(json.dumps({"coverage": round(cov, 2)}))

if __name__ == "__main__":
    main()
