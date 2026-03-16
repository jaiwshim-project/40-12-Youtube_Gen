@echo off
chcp 65001 > nul
cd /d C:\YouTube

echo.
echo ================================================
echo   YouTube 영상 올인원 자동화
echo ================================================
echo.
echo  1. Step 0  - 경쟁 영상 리서치 (Gemini)
echo  2. Step 1  - 대본 생성
echo  3. Step 2  - 재료 일괄 생성
echo  4. Step 3  - 이미지 자동 생성 (Imagen 3)
echo  5. Step 5  - 블로그 글 생성
echo  6. Step 6  - 영상 자동 빌드 (MoviePy)
echo  7. Step 7  - YouTube 업로드
echo  8. 출력 폴더 열기
echo  9. 종료
echo.
set /p choice="번호를 입력하세요: "

if "%choice%"=="1" goto research
if "%choice%"=="2" goto write
if "%choice%"=="3" goto generate
if "%choice%"=="4" goto images
if "%choice%"=="5" goto blog
if "%choice%"=="6" goto video
if "%choice%"=="7" goto upload
if "%choice%"=="8" goto open_output
if "%choice%"=="9" goto end

:research
echo.
echo [Step 0] 경쟁 영상 리서치
set /p source="소재 파일 경로 (Enter = input\grandpa_grandma_story.txt): "
if "%source%"=="" set source=input\grandpa_grandma_story.txt
python orchestrator.py --research "%source%"
pause
goto end

:write
echo.
echo [Step 1] 대본 생성
set /p source="소재 파일 경로 (Enter = input\grandpa_grandma_story.txt): "
if "%source%"=="" set source=input\grandpa_grandma_story.txt
python orchestrator.py --write "%source%"
pause
goto end

:generate
echo.
echo [Step 2] 재료 일괄 생성
echo.
echo  output\ 폴더 안의 타임스탬프 폴더명을 입력하세요.
echo  예시: 20260316_120000
echo.
set /p ts="타임스탬프: "
set /p source="소재 파일 경로 (Enter = input\grandpa_grandma_story.txt): "
if "%source%"=="" set source=input\grandpa_grandma_story.txt
set /p shortform="숏폼으로 만드시겠어요? (y/n, Enter = n): "
if /i "%shortform%"=="y" (
    python orchestrator.py "output\%ts%\00_script\script.txt" --source "%source%" --short
) else (
    python orchestrator.py "output\%ts%\00_script\script.txt" --source "%source%"
)
pause
goto end

:images
echo.
echo [Step 3] Imagen 3 이미지 자동 생성
echo.
set /p ts="타임스탬프 (예: 20260316_120000): "
python orchestrator.py --images "output\%ts%"
pause
goto end

:blog
echo.
echo [Step 5] 블로그 글 생성
set /p url="YouTube URL: "
set /p ts="출력 폴더 타임스탬프 (예: 20260316_120000): "
python orchestrator.py --blog "%url%" "output\%ts%"
pause
goto end

:video
echo.
echo [Step 6] 영상 자동 빌드 (MoviePy + Whisper)
echo.
set /p ts="타임스탬프 (예: 20260316_120000): "
python orchestrator.py --video "output\%ts%"
pause
goto end

:upload
echo.
echo [Step 7] YouTube 업로드
echo.
set /p ts="타임스탬프 (예: 20260316_120000): "
echo 공개 설정: private(비공개) / unlisted(링크공개) / public(전체공개)
set /p privacy="공개 설정 (Enter = private): "
if "%privacy%"=="" set privacy=private
python orchestrator.py --upload "output\%ts%" --privacy "%privacy%"
pause
goto end

:open_output
explorer output
goto end

:end
echo.
echo 완료!
