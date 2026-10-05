@echo off
REM ====================================================================
REM  run_test.bat  -  News_analytics.py ���� �׽�Ʈ ���� (����� ���)
REM
REM  �� ������ News_analytics.py �� "���� ����"(��������)�� �ֽ��ϴ�.
REM  ��ο� �ѱ�/������ �־ ������ �ʵ���, ���� �̸��� ���� ���� �ʰ�
REM  cmd �� ���� ������ ä�� �ִ� %~dp0(= �� bat ������ �ִ� ����)�� ���ϴ�.
REM
REM  ����: �� ������ CP949(ANSI)�� �����ؾ� �մϴ�. UTF-8�� �����ϸ�
REM        �ѱ� �κ��� ������ ������ ������� �ʽ��ϴ�.
REM ====================================================================
setlocal
cd /d "%~dp0"

call :find_python
if not defined PYTHON_EXE (
    echo [����] python.exe �� ã�� ���߽��ϴ�.
    echo        Python �Ǵ� Anaconda ��ġ �� �ٽ� �����ϼ���.
    pause
    exit /b 1
)

echo ����� Python  : %PYTHON_EXE%
echo ������ ��ũ��Ʈ: %~dp0News_analytics.py
echo.

"%PYTHON_EXE%" "%~dp0News_analytics.py" --debug %*
set RC=%errorlevel%

echo.
if not "%RC%"=="0" (
    echo [����] ���� �ڵ� %RC%
    echo        ModuleNotFoundError �� ���̸� News ������
    echo        install_requirements.bat �� ���� �� �� �����ϼ���.
) else (
    echo [�Ϸ�] ���� ����Ǿ����ϴ�.
)
pause
exit /b %RC%

:find_python
REM PATH ���� python.exe �� ã��, Microsoft Store ����(WindowsApps)�� �ǳʶݴϴ�.
set "PYTHON_EXE="
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo %%i | find /i "WindowsApps" >nul
    if errorlevel 1 if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
)
if not defined PYTHON_EXE if exist "C:\Anaconda3\python.exe" set "PYTHON_EXE=C:\Anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
goto :eof
