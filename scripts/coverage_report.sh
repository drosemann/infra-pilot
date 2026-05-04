#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage reporting for the infra package
pytest -m "unit or integration or e2e" --cov=infra --cov-report=xml:coverage.xml --cov-report=html:coverage_html --cov-report=term-missing

# Print a concise coverage summary for quick consumption
python3 scripts/coverage_report.py coverage.xml

# Point to the HTML report location
echo "HTML coverage report available at coverage_html/index.html"
