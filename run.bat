@echo off
chcp 65001 >nul
title Smart Duplicate Cleaner Pro
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║           Smart Duplicate Cleaner Pro v2.0                 ║
echo  ║        Gelişmiş Kopya Dosya Bulucu ve Temizleyici          ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo  Hazırlanıyor...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo  HATA: Uygulama başlatılamadı.
    echo  - Python yüklü mü? (python --version)
    echo  - Tkinter mevcut mu? (python -c "import tkinter")
    echo  - main.py dosyası bu klasörde mi?
    echo.
    pause
)