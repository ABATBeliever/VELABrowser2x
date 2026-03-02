@echo off
setlocal enabledelayedexpansion
echo VELA DevelopmentKit for win
echo.

cd /d %~dp0\..

where uv >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing uv...
    powershell -ExecutionPolicy Bypass -Command ^
        "iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex"
    if errorlevel 1 (
        echo [CRITICAL] Failed to install uv
        exit /b 1
    )
) else (
    echo [INFO] uv is already installed.
)

if not exist .venv (
    echo [INFO] Creating venv...
    uv venv --python 3.12
    if errorlevel 1 (
        echo [CRITICAL] Failed to Create venv
        exit /b 1
    )
) else (
    echo [INFO] venv is ok
)

echo [INFO] Get dependent packages...
uv pip install --upgrade pip
uv pip install pyside6 qtawesome packaging nuitka
if errorlevel 1 (
    echo [ERROR] Failed to install packages
    exit /b 1
)

echo.
echo [SUCCESS] 
echo.
echo Run VELA  :
echo uv run python VELABrowser.py
echo.
echo Build VELA:
echo call scripts/build.bat
echo ※完了後に、inno/setup.issを実行する必要があります。
echo 　InnoSetup(https://jrsoftware.org/isdl.php) をインストールしてくださいね。
echo.
echo もしも "FATAL: Error, cannot locate suitable C compiler."というメッセージを見た場合は、
echo "https://abatbeliever.net/app/VELABrowser/docs/?p=Windowsにおけるビルド環境の構築.txt"を参照ください。
echo.
cmd /k