#!/usr/bin/env python3
import json
import sys
import xml.etree.ElementTree as ET

def main(coverage_xml_path: str):
    tree = ET.parse(coverage_xml_path)
    root = tree.getroot()
    # The top-level 'coverage' element has a line-rate attribute as a float between 0 and 1
    line_rate = root.attrib.get("line-rate")
    try:
        percent = float(line_rate) * 100.0
    except Exception:
        percent = 0.0
    data = {"coverage": round(percent, 2)}
    print(json.dumps(data))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: coverage_report.py <coverage.xml>")
        sys.exit(2)
    main(sys.argv[1])
