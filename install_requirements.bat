@echo off
REM ====================================================================
REM  install_requirements.bat  -  최초 1회만 실행
REM  requirements.txt 의 패키지(kiwipiepy, wordcloud 등)를 설치합니다.
REM  이 파일은 News 폴더 최상단(requirements.txt 와 같은 폴더)에 있습니다.
REM
REM  주의: 이 파일은 CP949(ANSI)로 저장해야 합니다.
REM ====================================================================
setlocal
cd /d "%~dp0"

call :find_python
if not defined PYTHON_EXE (
    echo [오류] python.exe 를 찾지 못했습니다.
    pause
    exit /b 1
)

echo 사용할 Python : %PYTHON_EXE%
echo 설치 목록     : %~dp0requirements.txt
echo.

"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt"
set RC=%errorlevel%

echo.
if "%RC%"=="0" (
    echo [완료] 설치가 끝났습니다. 이제 실행파일\run_test.bat 을 실행해 보세요.
) else (
    echo [실패] 종료 코드 %RC% . 위 오류 메시지를 확인하세요.
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
