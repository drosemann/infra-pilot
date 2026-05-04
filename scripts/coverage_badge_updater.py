#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import re

README_PATH = Path(__file__).resolve().parents[1] / 'README.md'
COVERAGE_XML = Path(__file__).resolve().parents[1] / 'coverage.xml'

def read_coverage_percent(xml_path: Path) -> int:
    if not xml_path.exists():
        return 0
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        line_rate = root.attrib.get('line-rate')
        if line_rate is None:
            return 0
        val = float(line_rate) * 100.0
        return int(round(val))
    except Exception:
        return 0

def update_readme(readme_path: Path, percent: int) -> bool:
    if not readme_path.exists():
        return False
    content = readme_path.read_text(encoding='utf-8')
    # Replace the badge URL's numeric portion
    pattern = re.compile(r'(https://img\.shields\.io/badge/coverage-)(\d+)(%25-brightgreen)')
    new_part = f"{percent}"
    new_content, n = pattern.subn(r"\g<1>" + new_part + r"\g<3>", content)
    if n == 0:
        # If not found, try a broader replace on the entire badge URL line
        broad = re.sub(r'coverage-\d+%25-brightgreen', f'coverage-{percent}%25-brightgreen', content)
        if broad == content:
            return False
        new_content = broad
    readme_path.write_text(new_content, encoding='utf-8')
    return new_content != content

def main():
    percent = read_coverage_percent(COVERAGE_XML)
    changed = update_readme(README_PATH, percent)
    if changed:
        print(f"Updated README coverage badge to {percent}%")
        print("PROCEED to commit and push from CI if desired.")
        sys.exit(0)
    else:
        print("No README updates needed for coverage badge.")
        sys.exit(0)

if __name__ == '__main__':
    main()
