@echo off
REM ====================================================================
REM  run_test.bat  -  News_analytics.py 수동 테스트 실행 (디버그 모드)
REM
REM  이 파일은 News_analytics.py 와 "같은 폴더"(실행파일)에 있습니다.
REM  경로에 한글/공백이 있어도 깨지지 않도록, 폴더 이름을 직접 적지 않고
REM  cmd 가 실행 시점에 채워 주는 %~dp0(= 이 bat 파일이 있는 폴더)만 씁니다.
REM
REM  주의: 이 파일은 CP949(ANSI)로 저장해야 합니다. UTF-8로 저장하면
REM        한글 부분이 깨져서 명령이 실행되지 않습니다.
REM ====================================================================
setlocal
cd /d "%~dp0"

call :find_python
if not defined PYTHON_EXE (
    echo [오류] python.exe 를 찾지 못했습니다.
    echo        Python 또는 Anaconda 설치 후 다시 실행하세요.
    pause
    exit /b 1
)

echo 사용할 Python  : %PYTHON_EXE%
echo 실행할 스크립트: %~dp0News_analytics.py
echo.

"%PYTHON_EXE%" "%~dp0News_analytics.py" --debug %*
set RC=%errorlevel%

echo.
if not "%RC%"=="0" (
    echo [실패] 종료 코드 %RC%
    echo        ModuleNotFoundError 가 보이면 News 폴더의
    echo        install_requirements.bat 을 먼저 한 번 실행하세요.
) else (
    echo [완료] 정상 종료되었습니다.
)
pause
exit /b %RC%

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
