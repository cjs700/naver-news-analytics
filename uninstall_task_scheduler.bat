@echo off
REM ====================================================================
REM  uninstall_task_scheduler.bat
REM  매일 오전 9시 자동 실행 등록(NaverNewsAnalytics_0900)을 해제합니다.
REM
REM  주의: 이 파일은 CP949(ANSI)로 저장해야 합니다.
REM ====================================================================
setlocal
schtasks /Delete /TN "NaverNewsAnalytics_0900" /F
if %errorlevel% equ 0 (
    echo.
    echo [완료] 자동 실행 등록을 해제했습니다.
) else (
    echo.
    echo [알림] 등록된 작업이 없거나 삭제에 실패했습니다.
)
pause
