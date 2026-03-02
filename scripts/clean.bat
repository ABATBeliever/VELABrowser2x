@echo off
setlocal

cd /d %~dp0\..

echo [INFO] Cleanup...
del /f nuitka-crash-report.xml
rmdir /S /Q .venv
rmdir /S /Q "VELABrowser.build"
rmdir /S /Q "VELABrowser.dist"
rmdir /S /Q "VELABrowser.onefile-build"
rmdir /S /Q "__pycache__"

endlocal
exit /b