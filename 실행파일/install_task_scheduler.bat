@echo off
REM ====================================================================
REM  install_task_scheduler.bat
REM  News_analytics.py 를 매일 오전 9시에 자동 실행하도록
REM  Windows 작업 스케줄러(Task Scheduler)에 등록합니다.
REM
REM  이 파일을 더블클릭하세요. (실패하면 마우스 오른쪽 -> 관리자 권한으로 실행)
REM
REM  주의: 이 파일은 CP949(ANSI)로 저장해야 합니다. UTF-8로 저장하면
REM        한글 부분이 깨져서 명령이 실행되지 않습니다.
REM ====================================================================
setlocal
set "SCRIPT_DIR=%~dp0"
set "TASK_NAME=NaverNewsAnalytics_0900"

call :find_python
if not defined PYTHON_EXE (
    echo [오류] PATH 에서 python.exe 를 찾지 못했습니다.
    echo        이 파일을 메모장으로 열어 아래 줄의 경로를 직접 적고 다시 실행하세요.
    echo        예: set "PYTHON_EXE=C:\Anaconda3\python.exe"
    pause
    exit /b 1
)

echo 사용할 Python  : %PYTHON_EXE%
echo 실행할 스크립트: %SCRIPT_DIR%News_analytics.py
echo.

schtasks /Create /TN "%TASK_NAME%" ^
    /TR "\"%PYTHON_EXE%\" \"%SCRIPT_DIR%News_analytics.py\"" ^
    /SC DAILY /ST 09:00 /F

if %errorlevel% equ 0 (
    echo.
    echo [완료] 매일 오전 9시에 자동 실행되도록 등록했습니다.
    echo        등록 확인   : schtasks /Query /TN "%TASK_NAME%"
    echo        지금 1회 실행: schtasks /Run   /TN "%TASK_NAME%"
    echo        등록 해제   : News 폴더의 uninstall_task_scheduler.bat
    echo.
    echo [참고] 스크립트가 G 드라이브(Google Drive)에 있으므로, 예약 시각에
    echo        PC 가 켜져 있고 로그인 상태이며 Google Drive 가 마운트되어
    echo        있어야 정상 실행됩니다.
) else (
    echo.
    echo [실패] 작업 스케줄러 등록에 실패했습니다.
    echo        이 파일을 마우스 오른쪽 클릭 -^> 관리자 권한으로 실행 해 보세요.
)
pause
exit /b 0

:find_python
REM PATH 에서 python.exe 를 찾되, Microsoft Store 스텁(WindowsApps)은 건너뜁니다.
set "PYTHON_EXE="
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo %%i | find /i "WindowsApps" >nul
    if errorlevel 1 if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
)
if not defined PYTHON_EXE if exist "C:\Anaconda3\python.exe" set "PYTHON_EXE=C:\Anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
goto :eof
