#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[INFO] Cleanup..."

rm -f nuitka-crash-report.xml

rm -rf .venv

rm -rf "VELABrowser.build"
rm -rf "VELABrowser.dist"
rm -rf "VELABrowser.onefile-build"