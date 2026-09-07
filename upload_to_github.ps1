# ====================================================================
#  upload_to_github.ps1
#  G 드라이브(Google Drive)의 뉴스 분석 결과 중 CSV/TXT 와 코드만
#  D:\projects\Python\naver-news-analytics 저장소로 동기화한 뒤
#  GitHub(cjs700/naver-news-analytics)에 자동 커밋·업로드한다.
#
#  Windows 작업 스케줄러가 매일 10:00 에 실행한다.
#  (09:00 에 도는 News_analytics.py 분석이 끝난 뒤 여유를 두고 실행)
#
#  실행 기록: G:\...\News\logs\github_upload.log
#  수동 실행: 이 파일 우클릭 → "PowerShell에서 실행"
# ====================================================================
$ErrorActionPreference = "Stop"

$SRC = "G:\내 드라이브\03_데이터분석_실습노트북\News"
$DST = "D:\projects\Python\naver-news-analytics"
$LOG = Join-Path $SRC "logs\github_upload.log"
$GIT = "C:\Anaconda3\Library\bin\git.exe"

function Write-Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    try { Add-Content -Path $LOG -Value $line -Encoding UTF8 } catch { }
    Write-Output $line
}

try {
    Write-Log "===== 자동 업로드 시작 ====="

    # ── 0. 사전 점검 ────────────────────────────────────────────
    if (-not (Test-Path $SRC)) {
        Write-Log "[실패] 원본 폴더를 찾을 수 없습니다: $SRC"
        Write-Log "        Google Drive 가 마운트되지 않았거나 로그인이 풀렸을 수 있습니다."
        exit 1
    }
    if (-not (Test-Path $DST)) { Write-Log "[실패] 저장소 폴더 없음: $DST"; exit 1 }
    if (-not (Test-Path $GIT)) { Write-Log "[실패] git 실행파일 없음: $GIT"; exit 1 }

    # ── 1. 최상단 파일 동기화 ───────────────────────────────────
    #  README.md 는 저장소 전용 부록(A-1~A-5)이 붙어 있으므로 덮어쓰지 않는다.
    foreach ($f in @("insight_master.csv", "requirements.txt",
                     "install_requirements.bat", "uninstall_task_scheduler.bat")) {
        $s = Join-Path $SRC $f
        if (Test-Path $s) { Copy-Item $s (Join-Path $DST $f) -Force }
    }

    # ── 2. 실행 스크립트 동기화 ─────────────────────────────────
    foreach ($f in @("News_analytics.py", "install_task_scheduler.bat", "run_test.bat")) {
        $s = Join-Path $SRC "실행파일\$f"
        if (Test-Path $s) { Copy-Item $s (Join-Path $DST "실행파일\$f") -Force }
    }

    # ── 3. 언론사 oid 캐시 ──────────────────────────────────────
    $cache = Join-Path $SRC "_cache\press_oid_map.json"
    if (Test-Path $cache) { Copy-Item $cache (Join-Path $DST "_cache\press_oid_map.json") -Force }

    # ── 4. 연도 폴더의 CSV/TXT 만 폴더구조 유지하며 복사 ────────
    #  PNG 는 용량이 커서(하루 약 30MB) 제외한다. .gitignore 에서도 막고 있다.
    $copied = 0
    Get-ChildItem -Path $SRC -Directory | Where-Object { $_.Name -match '^\d{4}$' } | ForEach-Object {
        Get-ChildItem -Path $_.FullName -Recurse -File |
          Where-Object { $_.Extension -eq ".csv" -or $_.Extension -eq ".txt" } |
          ForEach-Object {
              $rel = $_.FullName.Substring($SRC.Length + 1)
              $target = Join-Path $DST $rel
              $dir = Split-Path $target -Parent
              if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
              Copy-Item $_.FullName $target -Force
              $copied++
          }
    }
    Write-Log "데이터 파일 $copied 개 동기화 완료"

    # ── 5. 변경사항 확인 ────────────────────────────────────────
    $status = & $GIT -C $DST status --porcelain
    if (-not $status) {
        Write-Log "[완료] 변경사항이 없어 커밋을 건너뜁니다."
        exit 0
    }
    $changed = ($status | Measure-Object).Count
    Write-Log "변경된 파일 $changed 개 발견"

    # ── 6. 커밋 ────────────────────────────────────────────────
    & $GIT -C $DST add -A
    if ($LASTEXITCODE -ne 0) { Write-Log "[실패] git add 오류 (exit $LASTEXITCODE)"; exit 1 }

    $today = Get-Date -Format "yyyy-MM-dd"
    $msg = "데이터 자동 업데이트 $today ($changed 개 파일)"
    & $GIT -C $DST commit -q -m $msg
    if ($LASTEXITCODE -ne 0) { Write-Log "[실패] git commit 오류 (exit $LASTEXITCODE)"; exit 1 }

    # ── 7. 업로드 ──────────────────────────────────────────────
    $push = (& $GIT -C $DST push origin main 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Write-Log "[실패] git push 오류 (exit $LASTEXITCODE): $push"
        Write-Log "        GitHub 인증이 풀렸을 수 있습니다. gh auth status 로 확인하세요."
        exit 1
    }

    $sha = (& $GIT -C $DST rev-parse --short HEAD).Trim()
    Write-Log "[성공] 커밋 $sha 업로드 완료 — $msg"
    Write-Log "        https://github.com/cjs700/naver-news-analytics"
    exit 0
}
catch {
    Write-Log "[실패] 예외 발생: $($_.Exception.Message)"
    exit 1
}
