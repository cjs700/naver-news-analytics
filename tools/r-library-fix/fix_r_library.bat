@echo off
REM ====================================================================
REM  fix_r_library.bat  -  double-click to repair the R package library
REM  (dplyr / rlang.dll "LoadLibrary failure"). Runs fix_r_library.R.
REM  This file is ASCII only on purpose (safe in any Windows code page).
REM ====================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   R library repair  -  dplyr / rlang
echo ============================================================
echo.

REM ---- 1) RStudio / R must be closed (loaded DLLs are locked) -------
set "BUSY="
for %%P in (rstudio.exe rsession.exe Rgui.exe Rterm.exe) do (
    tasklist /FI "IMAGENAME eq %%P" 2>nul | find /I "%%P" >nul && set "BUSY=%%P"
)
if defined BUSY (
    echo [STOP] %BUSY% is running.
    echo        Close RStudio and every R window completely, then run this file again.
    echo.
    pause
    exit /b 1
)

REM ---- 2) Find Rscript.exe --------------------------------------------
set "RSCRIPT="
if exist "C:\R\R-4.6.1\bin\Rscript.exe" set "RSCRIPT=C:\R\R-4.6.1\bin\Rscript.exe"
if not defined RSCRIPT for /d %%D in ("C:\R\R-*") do if exist "%%D\bin\Rscript.exe" set "RSCRIPT=%%D\bin\Rscript.exe"
if not defined RSCRIPT for /d %%D in ("%ProgramFiles%\R\R-*") do if exist "%%D\bin\Rscript.exe" set "RSCRIPT=%%D\bin\Rscript.exe"
if not defined RSCRIPT for /f "delims=" %%W in ('where Rscript 2^>nul') do if not defined RSCRIPT set "RSCRIPT=%%W"
if not defined RSCRIPT (
    echo [ERROR] Rscript.exe not found. Edit the RSCRIPT line in this file.
    pause
    exit /b 1
)
echo Rscript : %RSCRIPT%
echo Script  : %~dp0fix_r_library.R
echo.

REM ---- 3) Run the repair script ---------------------------------------
"%RSCRIPT%" "%~dp0fix_r_library.R"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo ============================================================
    echo   DONE. Open RStudio and run:  library^(dplyr^)
    echo ============================================================
) else (
    echo ============================================================
    echo   FAILED ^(exit code %RC%^). Send the log file to Claude:
    echo   C:\R\fix_r_library_log.txt
    echo ============================================================
)
if exist "C:\R\fix_r_library_log.txt" start "" notepad "C:\R\fix_r_library_log.txt"
echo.
pause
exit /b %RC%
