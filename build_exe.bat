@echo off
REM ============================================================
REM  Reconstruieste BetterLife.exe din sursa.
REM  Ruleaza dupa ce ai modificat app.py / core.py / ui.html / foods.py.
REM ============================================================
cd /d "%~dp0"

echo Instalez dependintele de build...
pip install pyinstaller pyyaml tzdata pywebview

echo.
echo Construiesc BetterLife.exe...
pyinstaller --noconfirm --onefile --windowed --name BetterLife ^
    --icon "icon.ico" ^
    --add-data "config.yaml;." ^
    --add-data "ui.html;." ^
    --add-data "workout.json;." ^
    --collect-all webview ^
    --collect-all tzdata ^
    app.py

if exist "dist\BetterLife.exe" (
    copy /Y "dist\BetterLife.exe" "BetterLife.exe" >nul
    echo.
    echo GATA! Ai BetterLife.exe in folderul proiectului. Dublu-click ca sa-l deschizi.
) else (
    echo.
    echo EROARE: build-ul a esuat. Verifica mesajele de mai sus.
)
pause