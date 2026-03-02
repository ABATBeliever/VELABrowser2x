#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APPDIR="$ROOT_DIR/VELABrowser.AppDir"
BIN_DEST="$APPDIR/usr/bin/VELABrowser"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
OUTPUT="$ROOT_DIR/VELABrowser-x64.AppImage"

if [ ! -f "$APPIMAGETOOL" ]; then
    echo "[INFO] fetching AppImageTool"
    curl -fsSL "$APPIMAGETOOL_URL" -o "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
    echo "[INFO] fetched AppImageTool: $APPIMAGETOOL"
else
    echo "[INFO] AppImageTool is OK: $APPIMAGETOOL"
fi

echo "[INFO] Building binary with nuitka..."
cd "$ROOT_DIR"

uv run nuitka \
    --standalone --onefile \
    --enable-plugin=pyside6 \
    --company-name=ABATBeliever \
    --product-name="VELA Browser Praxis" \
    --file-description="VELA Browser Praxis WebBrowser" \
    --nofollow-import-to=PySide6.QtBluetooth \
    --nofollow-import-to=PySide6.QtNfc \
    --nofollow-import-to=PySide6.QtSensors \
    --nofollow-import-to=PySide6.QtSerialPort \
    --nofollow-import-to=PySide6.QtSerialBus \
    --nofollow-import-to=PySide6.QtPositioning \
    --nofollow-import-to=PySide6.QtMultimedia \
    --nofollow-import-to=PySide6.QtMultimediaWidgets \
    --nofollow-import-to=PySide6.Qt3DCore \
    --nofollow-import-to=PySide6.Qt3DRender \
    --nofollow-import-to=PySide6.Qt3DInput \
    --nofollow-import-to=PySide6.Qt3DAnimation \
    --nofollow-import-to=PySide6.QtCharts \
    --nofollow-import-to=PySide6.QtDataVisualization \
    --nofollow-import-to=PySide6.QtQuick \
    --nofollow-import-to=PySide6.QtQml \
    --nofollow-import-to=PySide6.QtQuickWidgets \
    --nofollow-import-to=PySide6.QtRemoteObjects \
    --nofollow-import-to=PySide6.QtScxml \
    --nofollow-import-to=PySide6.QtWebSockets \
    --nofollow-import-to=PySide6.QtXml \
    --nofollow-import-to=PySide6.QtSvg \
    --nofollow-import-to=PySide6.QtSvgWidgets \
    --nofollow-import-to=PySide6.QtHelp \
    --nofollow-import-to=PySide6.QtDesigner \
    --nofollow-import-to=PySide6.QtUiTools \
    --nofollow-import-to=tkinter \
    --nofollow-import-to=test \
    --nofollow-import-to=unittest \
    --nofollow-import-to=distutils \
    --nofollow-import-to=xml.etree \
    --nofollow-import-to=xml.dom \
    --nofollow-import-to=xml.sax \
    VELABrowser.py

echo "[INFO] Building binary OK"

NUITKA_OUTPUT="$ROOT_DIR/VELABrowser.bin"
if [ ! -f "$NUITKA_OUTPUT" ]; then
    echo "[ERROR] Failed to find VELABrowser.bin: $NUITKA_OUTPUT"
    exit 1
fi

mkdir -p "$APPDIR/usr/bin"
cp "$NUITKA_OUTPUT" "$BIN_DEST"

echo "[INFO] chmod..."
chmod +x "$APPDIR/AppRun"
chmod +x "$BIN_DEST"
chmod +x "$APPDIR/vela.png"

echo "[INFO] Building .AppImage with AppImageTool..."
cd "$ROOT_DIR"

ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"

chmod +x "$OUTPUT"

echo ""
echo "[INFO] Build Sucsess! [x64]"
