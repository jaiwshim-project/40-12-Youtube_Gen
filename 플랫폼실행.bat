@echo off
chcp 65001 > nul
cd /d C:\YouTube
echo.
echo  YouTube 자동화 플랫폼 시작 중...
echo  브라우저: http://localhost:5000
echo.
start "" http://localhost:5000
python app.py
pause
