@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
  echo PySide6をインストールします...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo インストールできませんでした。Pythonの設定をご確認ください。
    pause
    exit /b 1
  )
)
python app.py %*
if errorlevel 1 pause
