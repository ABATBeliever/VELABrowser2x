#!/usr/bin/env bash
set -e

echo "VELA DevelopmentKit for rasp
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if ! command -v uv >/dev/null 2>&1; then
    echo "[INFO] Installing uv..."
    curl -Ls https://astral.sh/uv/install.sh | sh
    echo "Please re-open to Use PATH"
    exit 0
else
    echo "[INFO] uv is already installed."
fi

export PATH="$HOME/.cargo/bin:$PATH"

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating venv..."
    uv venv --python 3.12
else
    echo "[INFO] venv is ok"
fi

echo "[INFO] Get dependent packages..."
uv pip install --upgrade pip
uv pip install pyside6 qtawesome packaging nuitka

echo
echo "[SUCCESS]"
echo
echo "Run VELA  :"
echo "uv run python VELABrowser.py"
echo
echo "Build VELA:"
echo "uv run nuitka \\"
echo "  --standalone \\"
echo "  --onefile \\"
echo "  --enable-plugin=pyside6 \\"
echo "  --follow-imports \\"
echo "  VELABrowser.py"
echo

exec bash
